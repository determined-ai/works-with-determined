from typing import NamedTuple

import kfp
from kfp import dsl
from kfp.components import func_to_container_op, InputPath, OutputPath
import os


def download_inference_data(bucket: str) -> str:
    """Download data from S3"""
    import boto3
    import os
    s3 = boto3.resource('s3')

    def download_s3_folder(bucket_name, s3_folder, local_dir):
        """
        Download the contents of a folder directory
        Args:
            bucket_name: the name of the s3 bucket
            s3_folder: the folder path in the s3 bucket
            local_dir: a relative or absolute directory path in the local file system
        """
        bucket = s3.Bucket(bucket_name)
        for obj in bucket.objects.filter(Prefix=s3_folder):
            target = obj.key if local_dir is None \
                else os.path.join(local_dir, os.path.basename(obj.key))
            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            bucket.download_file(obj.key, target)
            print(obj.key)

    local_path = "/data/"
    download_s3_folder(bucket, '', local_path)
    return local_path


download_inference_data_op = func_to_container_op(
    download_inference_data, packages_to_install=["boto3"]
)


def create_ped_inference_op(
    detmaster: str,
    model_name: str,
    model_version: int,
    data_path: str,
    volume: dsl.PipelineVolume,
):
    command = [
        "python",
        "inference.py",
        f'{data_path}',
        f'{model_name}',
        f'{detmaster}',
        f'{model_version}',
    ]
    return dsl.ContainerOp(
        name='Questing Answering Batch Inference',
        image='davidhershey/squad-inference:1.4',
        command=command,
        file_outputs={
            'predictions': '/tmp/outputs.txt',
        },
        pvolumes={"/data/": volume},
    )


@dsl.pipeline(
    name="Question Answering Batch Inference", description="Inference with a Determined Model"
)
def inference_pipeline(
    detmaster,
    data_bucket='david-question-answering',
    model_name="question-answering",
    model_version=0,
):
    volume_op = dsl.VolumeOp(
        name="create pipeline volume",
        resource_name="mlrepo-pvc",
        modes=["ReadWriteOnce"],
        size="3Gi",
    )
    download = (
        download_inference_data_op(data_bucket)
        .add_pvolumes({"/data/": volume_op.volume})
    )
    ped_inference_op = create_ped_inference_op(
        detmaster,
        model_name,
        model_version,
        download.output,
        volume_op.volume,
    )


if __name__ == "__main__":
    # Compiling the pipeline
    kfp.compiler.Compiler().compile(inference_pipeline, 'qa_inference.yaml')
