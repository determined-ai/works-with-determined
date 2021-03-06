import argparse
import logging
import json
import os
import subprocess
import re
import tempfile

from git import Repo
from determined.experimental import Determined


logging.basicConfig(level=logging.INFO)


def get_validation_metric(experiment_id, determined_master):
    print('Getting Checkpoint')
    exp = Determined(master=determined_master).get_experiment(experiment_id)
    checkpoint = exp.top_checkpoint()
    print('Downloading Checkpoint')
    path = checkpoint.download()
    print('Loading Metadata')
    metadata = json.load(open(os.path.join(path, 'metadata.json'), 'r'))
    metric = metadata['experiment_config']['searcher']['metric']
    best_metric = checkpoint.validation['metrics']['validation_metrics'][metric]
    return best_metric


def clone_and_create_experiment(ds, **kwargs):
    # print(kwargs)
    # return 1
    repo = kwargs['params']['git_repo']
    config = kwargs['params']['config']
    context = kwargs['params']['context']
    det_master = kwargs['params']['det_master']
    os.makedirs('/tmp/airflow/', exist_ok=True)
    clone_dir = tempfile.mkdtemp(prefix='/tmp/airflow/')
    Repo.clone_from(repo, clone_dir)
    config_path = os.path.join(clone_dir, config)
    context_path = os.path.join(clone_dir, context)
    # Submit determined experiment via CLI
    cmd = ["det", "-m", det_master, "e", "create", config_path, context_path]
    submit = subprocess.run(cmd, capture_output=True)
    output = str(submit.stdout)
    print(output)
    print(str(submit.stderr))
    experiment_id = int(re.search("Created experiment (\d+)", output)[1])
    logging.info(f'Created Experiment {experiment_id}')
    return experiment_id


def wait_for_experiment(ds, **kwargs):
    det_master = kwargs['params']['det_master']
    task_instance = kwargs['task_instance']
    experiment_id = task_instance.xcom_pull(task_ids='train')
    # Wait for experiment to complete via CLI
    wait = subprocess.run(["det", "-m", det_master, "e", "wait", str(experiment_id)])
    logging.info(f"Experiment {experiment_id} completed!")
    return get_validation_metric(experiment_id, det_master)
