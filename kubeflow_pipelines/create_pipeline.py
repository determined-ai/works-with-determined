from typing import NamedTuple

import kfp
from kfp import dsl
from kfp.components import func_to_container_op, InputPath, OutputPath
import os


def clone_mlrepo(repo_url: str, branch: str, volume: dsl.PipelineVolume):
    image = "alpine/git:latest"

    commands = [
        f"git clone --single-branch --branch {branch} {repo_url} /src/mlrepo/",
        f"cd /src/mlrepo/",
        f"ls",
    ]

    op = dsl.ContainerOp(
        name="git clone",
        image=image,
        command=["sh"],
        arguments=["-c", " && ".join(commands)],
        pvolumes={"/src/": volume},
    )

    return op


def run_det_and_wait(detmaster: str, config: str, context: str) -> int:
    # Submit determined experiment via CLI
    import logging
    import os
    import re
    import subprocess

    logging.basicConfig(level=logging.INFO)
    os.environ['DET_MASTER'] = detmaster

    repo_dir = "/src/mlrepo/"

    config = os.path.join(repo_dir, config)
    context = os.path.join(repo_dir, context)
    cmd = ["det", "e", "create", config, context]
    submit = subprocess.run(cmd, capture_output=True)
    output = str(submit.stdout)
    experiment_id = int(re.search("Created experiment (\d+)", output)[1])
    logging.info(f"Created Experiment {experiment_id}")

    # Wait for experiment to complete via CLI
    wait = subprocess.run(["det", "e", "wait", str(experiment_id)])
    logging.info(f"Experiment {experiment_id} completed!")
    return experiment_id


run_det_and_wait_op = func_to_container_op(
    run_det_and_wait, base_image="davidhershey/detcli:1.9"
)


def register(detmaster: str, experiment_id: int, model_name: str) -> bool:
    # Submit determined experiment via CLI
    from determined.experimental import Determined
    import os

    os.environ['DET_MASTER'] = detmaster

    def get_validation_metric(checkpoint):
        metrics = checkpoint.validation['metrics']
        config = checkpoint.experiment_config
        searcher = config['searcher']
        smaller_is_better = bool(searcher['smaller_is_better'])
        metric_name = searcher['metric']
        metric = metrics['validationMetrics'][metric_name]
        return (metric, smaller_is_better)

    def is_better(c1, c2):
        m1, smaller_is_better = get_validation_metric(c1)
        m2, _ = get_validation_metric(c2)
        if smaller_is_better and m1 < m2:
            return True
        return False

    d = Determined()
    checkpoint = d.get_experiment(experiment_id).top_checkpoint()
    try:
        model = d.get_model(model_name)
    except:  # Model not yet in registry
        print(f'Registering new Model: {model_name}')
        model = d.create_model(model_name)

    print(f'Registering new version: {model_name}')
    model.register_version(checkpoint.uuid)
    return True


register_op = func_to_container_op(
    register, base_image="davidhershey/detcli:1.9"
)


def create_seldon_op(
    detmaster: str,
    deployment_name: str,
    deployment_namespace: str,
    model_name: str,
    image: str,
):
    command = [
        "python",
        "create_seldon_deployment.py",
        f'{deployment_name}',
        f'{deployment_namespace}',
        f'{detmaster}',
        f'{model_name}',
        '--image',
        f'{image}',
    ]
    return dsl.ContainerOp(
        name='Create Seldon Deployment',
        image='davidhershey/seldon-create:1.2',
        command=command,
        file_outputs={
            'endpoint': '/tmp/endpoint.txt',
        }
    )


@func_to_container_op
def print_op(message: str):
    """Print a message."""
    print(message)


@dsl.pipeline(
    name="Determined Train and Deploy",
    description="Train a model with Determined, deploy the result to Seldon"
)
def det_train_pipeline(
    detmaster,
    mlrepo="https://github.com/determined-ai/determined.git",
    branch="0.13.0",
    config="examples/official/trial/mnist_pytorch/const.yaml",
    context="examples/official/trial/mnist_pytorch/",
    model_name="mnist-prod",
    deployment_name="mnist-prod-kf",
    deployment_namespace="david",
    image="davidhershey/seldon-mnist:1.6"
):
    volume_op = dsl.VolumeOp(
        name="create pipeline volume",
        resource_name="mlrepo-pvc",
        modes=["ReadWriteOnce"],
        size="3Gi",
    )
    clone = clone_mlrepo(mlrepo, branch, volume_op.volume)
    train = (
        run_det_and_wait_op(detmaster, config, context)
        .add_pvolumes({"/src/": clone.pvolume})
        .after(clone)
    )
    register = (
        register_op(detmaster, train.output, model_name)
        .after(train)
    )
    deploy = create_seldon_op(
        detmaster,
        deployment_name,
        deployment_namespace,
        model_name,
        image,
    ).after(register)


if __name__ == "__main__":
    # Compiling the pipeline
    kfp.compiler.Compiler().compile(det_train_pipeline, 'train_and_deploy.yaml')
