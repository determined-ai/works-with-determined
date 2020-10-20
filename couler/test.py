import os

import couler.argo as couler
from couler.argo_submitter import ArgoSubmitter
from couler.core.templates.volume_claim import VolumeClaimTemplate
from couler.core.templates.volume import VolumeMount
from couler.core.syntax import create_workflow_volume


def touch_op(data_mount):
    command = ["touch", os.path.join(data_mount.mount_path, 'hello_world.txt')]
    return couler.run_container(
        image="alpine:3.12.0", command=command, volume_mounts=[data_mount]
    )


def ls_op(data_mount):
    command = ["ls", data_mount.mount_path]
    return couler.run_container(
        image="alpine:3.12.0", command=command, volume_mounts=[data_mount]
    )


volume_name = "pvc-test"
volume_path = "/data/"
pvc = VolumeClaimTemplate(volume_name)
mount = VolumeMount(volume_name, volume_path)
create_workflow_volume(pvc)
touch_op(mount)
ls_op(mount)

submitter = ArgoSubmitter(namespace="argo")
couler.run(submitter=submitter)
