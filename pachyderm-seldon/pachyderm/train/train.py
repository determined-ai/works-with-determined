from determined.common.experimental.experiment import ExperimentState
from determined.experimental import client
import os
import git
import argparse
import yaml

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

def run_experiment(configfile, datapath):
    print(f"Creating experiment on DeterminedAI...")
    client.login(
        master  = os.getenv("DET_MASTER"),
        user    = os.getenv("DET_USER"),
        password= os.getenv("DET_PASSWORD"),
    )

    try:
        exp = client.create_experiment(configfile, datapath)
        print(f"Created experiment with id='{exp.id}'. Waiting for its completion...")

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

def get_checkpoint(exp):
    try:
        return exp.top_checkpoint()
    except AssertionError:
        return None

# =====================================================================================

def get_or_create_model(client, model_name):

    models = client.get_models(name=model_name)

    if len(models) > 0:
        print(f"Model already present. Updating it : {model_name}")
        model = client.get_models(name=model_name)[0]
    else:
        print(f"Creating a new model : {model_name}")
        model = client.create_model(model_name)

    return model

# =====================================================================================

def register_checkpoint(checkpoint, model, job_id):
    print(f"Registering checkpoint on model : {model.name}")
    version = model.register_version(checkpoint.uuid)
    version.set_name(job_id)
    checkpoint.download("/pfs/out/checkpoint")
    print("Checkpoint registered and downloaded to output repository")

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
    exp    = run_experiment(config, workdir)

    if exp is None:
        print("Aborting pipeline as experiment did not succeed")
        return

    # --- Get best checkpoint from experiment. It may not exist if the experiment did not succeed

    checkpoint = get_checkpoint(exp)

    if checkpoint is None:
        print("No checkpoint found (probably there was no data). Aborting pipeline")
        return

    # --- Now, register checkpoint on model and download it

    model = get_or_create_model(client, args.model)
    register_checkpoint(checkpoint, model, job_id)

    print(f"Ending pipeline: name='{pipeline}', repo='{args.repo}', job_id='{job_id}'")

# =====================================================================================


if __name__ == "__main__":
    main()
