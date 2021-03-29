import subprocess
from subprocess import PIPE
import os
import re

def setup():

    install_determined = ["pip", "install", "determined-cli"]
    cli = subprocess.run(install_determined)

def submit(det_master, config_file, context):

    start_experiment = ["det", "-m", det_master, "e", "create", config_file, context, "-f"]

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

def get_metrics(det_master, experiment_id):

    awk = "'NR == 2 { print $4 }'"
    cmd = f"det e lc --best 1 --csv {experiment_id} | awk -F, {awk}"
    ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = ps.communicate()[0]
    metric = output.decode('UTF-8')

    ps.terminate()
    ps.wait()

    return metric