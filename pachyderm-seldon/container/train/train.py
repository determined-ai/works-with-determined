from determined.common.experimental.experiment import ExperimentState
from determined.common.experimental import experiment
from determined.experimental import Determined

import os
import git
import argparse
import yaml

# =====================================================================================

class DeterminedClient(Determined):
    def __init__(self, master, user, password):
        super().__init__(master=master, user=user, password=password)

    def continue_experiment(self, config, parent_id, checkpoint_uuid):
        config["searcher"]["source_checkpoint_uuid"] = checkpoint_uuid
        resp = self._session.post(
            "/api/v1/experiments",
            json={
                "activate": True,
                "config": yaml.safe_dump(config),
                "parentId": parent_id,
            },
        )

        exp_id = resp.json()["experiment"]["id"]
        exp = experiment.ExperimentReference(exp_id, self._session)

        return exp

# =====================================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="Determined AI Experiment Runner")

    parser.add_argument(
        "--config",
        type=str,
        help="Determined's experiment configuration file",
    )

    parser.add_argument(
        "--git-url",
        type=str,
        help="Git URL of the repository containing the model code",
    )

    parser.add_argument(
        "--git-ref",
        type=str,
        help="Git Commit/Tag/Branch to use",
    )

    parser.add_argument(
        "--sub-dir",
        type=str,
        help="Subfolder to experiment files",
    )

    parser.add_argument(
        "--repo",
        type=str,
        help="Name of the Pachyderm's repository containing the dataset",
    )

    parser.add_argument(
        "--model",
        type=str,
        help="Name of the model on DeterminedAI to create/update",
    )

    return parser.parse_args()

# =====================================================================================

def clone_code(repo_url, ref, dir):
    print(f"Cloning code from: {repo_url}@{ref} --> {dir}")
    if os.path.isdir(dir):
        repo = git.Repo(dir)
        repo.remotes.origin.fetch()
    else:
        repo = git.Repo.clone_from(repo_url, dir)
    repo.git.checkout(ref)

# =====================================================================================

def read_config(conf_file):
    print(f"Reading experiment config file: {conf_file}")
    config = {}
    with open(conf_file, "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return config

# =====================================================================================

def setup_config(config_file, repo, pipeline, job_id):
    config = read_config(config_file)
    config["data"]["pachyderm"]["host"]   = os.getenv("PACHD_LB_SERVICE_HOST")
    config["data"]["pachyderm"]["port"]   = os.getenv("PACHD_LB_SERVICE_PORT")
    config["data"]["pachyderm"]["repo"]   = repo
    config["data"]["pachyderm"]["branch"] = job_id
    config["data"]["pachyderm"]["token"]  = os.getenv("PAC_TOKEN")

    config["labels"] = [ repo, job_id, pipeline ]

    return config

# =====================================================================================

def create_client():
    return DeterminedClient(
        master  = os.getenv("DET_MASTER"),
        user    = os.getenv("DET_USER"),
        password= os.getenv("DET_PASSWORD"),
    )

# =====================================================================================

def execute_experiment(client, configfile, code_path, checkpoint):
    try:
        if checkpoint is None:
            parent_id = None
            exp = client.create_experiment(configfile, code_path)
        else:
            parent_id = checkpoint.training.experiment_id
            exp = client.continue_experiment(configfile, parent_id, checkpoint.uuid)

        print(f"Created experiment with id='{exp.id}' (parent_id='{parent_id}'). Waiting for its completion...")

        state = exp.wait()
        print(f"Experiment with id='{exp.id}' ended with the following state: {state}")

        if state == ExperimentState.COMPLETED:
            return exp
        else:
            return None
    except AssertionError:
        print("Experiment exited with abnormal state")
        return None

# =====================================================================================

def run_experiment(client, configfile, code_path, model):
    version = model.get_version()

    if version is None:
        print("Creating a new experiment on DeterminedAI...")
        return execute_experiment(client, configfile, code_path, None)
    else:
        print("Continuing experiment on DeterminedAI...")
        return execute_experiment(client, configfile, None, version.checkpoint)

# =====================================================================================

def get_checkpoint(exp):
    try:
        return exp.top_checkpoint()
    except AssertionError:
        return None

# =====================================================================================

def get_or_create_model(client, model_name, pipeline, repo):

    models = client.get_models(name=model_name)

    if len(models) > 0:
        print(f"Model already present. Updating it : {model_name}")
        model = client.get_models(name=model_name)[0]
    else:
        print(f"Creating a new model : {model_name}")
        model = client.create_model(name=model_name, labels=[ pipeline, repo], metadata={
            "pipeline": pipeline,
            "repository": repo
        })

    return model

# =====================================================================================

def register_checkpoint(checkpoint, model, job_id):
    print(f"Registering checkpoint on model : {model.name}")
    version = model.register_version(checkpoint.uuid)
    version.set_name(job_id)
    version.set_notes("Job_id/commit_id = " + job_id)

    checkpoint.download("/pfs/out/checkpoint")
    print("Checkpoint registered and downloaded to output repository")

# =====================================================================================

def write_model_info(file, model_name, model_version, pipeline, repo):
    print(f"Writing model information to file: {file}")

    model = dict()
    model["name"]     = model_name
    model["version"]  = model_version
    model["pipeline"] = pipeline
    model["repo"]     = repo

    with open(file, "w") as stream:
        try:
            yaml.safe_dump(model, stream)
        except yaml.YAMLError as exc:
            print(exc)

# =====================================================================================

def main():
    # --- Retrieve useful info from environment

    job_id    = os.getenv("PACH_JOB_ID")
    pipeline  = os.getenv("PPS_PIPELINE_NAME")
    args      = parse_args()

    print(f"Starting pipeline: name='{pipeline}', repo='{args.repo}', job_id='{job_id}'")

    # --- Download code repository

    local_repo = os.path.join(os.getcwd(), "code-repository")
    clone_code(args.git_url, args.git_ref, local_repo)

    # --- Points to the correct subfolder inside the cloned repo

    if args.sub_dir:
        workdir = os.path.join(local_repo, args.sub_dir)
    else:
        workdir = local_repo

    config_file = os.path.join(workdir, args.config)

    # --- Read and setup experiment config file. Then, run experiment

    config = setup_config(config_file, args.repo, pipeline, job_id)
    client = create_client()
    model  = get_or_create_model(client, args.model, pipeline, args.repo)
    exp    = run_experiment(client, config, workdir, model)

    if exp is None:
        print("Aborting pipeline as experiment did not succeed")
        return

    # --- Get best checkpoint from experiment. It may not exist if the experiment did not succeed

    checkpoint = get_checkpoint(exp)

    if checkpoint is None:
        print("No checkpoint found (probably there was no data). Aborting pipeline")
        return

    # --- Now, register checkpoint on model and download it

    register_checkpoint(checkpoint, model, job_id)
    write_model_info("/pfs/out/model-info.yaml", args.model, job_id, pipeline, args.repo)

    print(f"Ending pipeline: name='{pipeline}', repo='{args.repo}', job_id='{job_id}'")

# =====================================================================================


if __name__ == "__main__":
    main()
