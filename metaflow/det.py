import subprocess
from subprocess import PIPE
import os
import re

def setup(det_version, repo_url, example_dir, config_file, local_repo_dir):

    clone_command = ["git", "clone", "--single-branch", "--branch", det_version, repo_url, local_repo_dir]
    clone_repo = subprocess.run(clone_command)

    install_determined = ["pip", "install", "determined-cli"]
    cli = subprocess.run(install_determined)

    config = os.path.join(local_repo_dir, example_dir, config_file)
    context = os.path.join(local_repo_dir, example_dir)

    return config, context

def submit(det_master, config, context):

    start_experiment = ["det", "-m", det_master, "e", "create", config, context, "-f"]

    experiment_id = ''
    env = dict(os.environ)
    env['PYTHONUNBUFFERED']='1'
    p = subprocess.Popen(start_experiment, stdout=PIPE, env=env)

    try:
        while True:
            line = p.stdout.readline()
            if not line:
                break
            line = line.decode("utf-8")

            if experiment_id == '':
                try:
                    experiment_id = int(re.search("Created experiment (\d+)", line)[1])
                except:
                    pass

            print(line, end='', flush=True)

        print(f"Experiment {experiment_id} completed!")

    except KeyboardInterrupt:
        print("User exited")
        exit_command = ["det", "-m", det_master, "e", "kill", str(experiment_id)]
        subprocess.run(exit_command)

    finally:
        p.terminate()
        p.wait()

    return experiment_id
