import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter
from couler.core.templates.volume_claim import VolumeClaimTemplate
from couler.core.templates.volume import VolumeMount
from couler.core.syntax import create_workflow_volume


def download_op(bucket_name, data_mount):
    command = [
        "python",
        "download_bucket.py",
        bucket_name,
        data_mount.mount_path
    ]
    return couler.run_container(
        image="davidhershey/boto:1.1", command=command, volume_mounts=[data_mount]
    )


def ped_inference_op(
    detmaster: str,
    model_name: str,
    model_version: int,
    volume: VolumeMount,
):
    command = [
        "python",
        "inference.py",
        f'{data_mount.mount_path}',
        f'{model_name}',
        f'{detmaster}',
        f'{model_version}'
    ]
    return couler.run_container(
        image='davidhershey/pedestrian-batch:1.3',
        command=command,
        volume_mounts=[data_mount]
    )


volume_name = "pvc-test"
volume_path = "/data/"
pvc = VolumeClaimTemplate(volume_name)
mount = VolumeMount(volume_name, volume_path)
create_workflow_volume(pvc)
download_op("david-pedestrian-detection-examples", mount)
ls_op(mount)

submitter = ArgoSubmitter(namespace="argo")
couler.run(submitter=submitter)
