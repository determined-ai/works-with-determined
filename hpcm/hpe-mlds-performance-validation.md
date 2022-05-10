# HPE ML Dev Sys Performance Validation Guide

This guide provides steps for the installation teams to validate the performance of HPE ML Development System ("System").

This performance validation guide has tested on the following versions:

| Supported Versions |
|--------------------|
| RHEL 8.5           |
| HPCM 1.7           |
| ML Dev Env 0.17.14 |

This guide assumes:

1. the installation team is familiar with general debugging skills on RHEL.
2. the installation team is familiar with HPCM.
3. the installation team knows what an HPE ML Dev Sys is.
4. the System is already installed with SW.
5. the following files are downloaded:
   - `hpe-mlde-install-validation-taskenvs-0.17.14.tar`
   - `mlds-<cluster-gpus>-gpu-reference.json` You need to download the reference json for the same number of GPUs as the GPU number of the cluster that you are installing.

With this guide, you should be able to run the performance validation tests and get the result of whether the cluster that you are installing pass the performance validation tests.

## Step 1 - Prerequisites

Before running the performance validation script, ensure that the master is running. You should also check if the resource pools have the correct number of connected agents by checking the WebUI.

## Step 2 - Transferring Performance Validation Task Environment to Agent Nodes 

Copy the tar ball files to all agent compute nodes on Apollo 6500.

Assume you are on the agent compute nodes, use the following commands to load Docker images from those tar ball files.

```bash
docker load -i hpe-mlde-install-validation-taskenvs-0.17.14.tar
```

Run the following commands to check if the images are loaded:

```bash
$ docker images
REPOSITORY                                     TAG                                                       IMAGE ID            CREATED             SIZE
determinedai/hpecaide-agent                    0.17.15                                                   4afe089f8dcf        2 days ago          98.6MB
determinedai/install-validation-transformers   0.17.14                                                   6739bbb639d1        2 weeks ago         24.8GB
determinedai/install-validation-mmdetection    0.17.14                                                   df9f8d07aae3        2 weeks ago         25.1GB
determinedai/environments                      cuda-11.3-pytorch-1.10-lightning-1.5-tf-2.8-gpu-0.17.12   2647c83f896e        3 weeks ago         15.9GB
determinedai/environments                      cuda-11.3-pytorch-1.10-lightning-1.5-tf-2.8-gpu-83dbcaa   2647c83f896e        3 weeks ago         15.9GB
nvcr.io/nvidia/k8s/dcgm-exporter               2.3.2-2.6.3-ubuntu20.04                                   009d8c29385c        2 months ago        570MB
fluent/fluent-bit                              1.6                                                       672c60a7ab2a        15 months ago       78.3MB
nvidia/cuda                                    11.0-base                                                 2ec708416bb8        20 months ago       122MB
gcr.io/cadvisor/cadvisor                       v0.36.0                                                   7414b6ed960c        22 months ago       184MB
```

You should see similar results as above. The images should include `determinedai/install-validation-transformers:0.17.14` and `determinedai/install-validation-mmdetection:0.17.14`

## Step 3 - Submitting Performance Validation tests on Login Node

Assuming you are on the login node, use the following commands to submit performance validation jobs:

```bash
# Set the cluster total GPUs
export CLUSTER_GPUS= 
# Set the per node GPUs
export PER_NODE_GPUS= 
# Set the master address to be the IP of the node of the hostname `master`
export MASTER_ADDR=$(/opt/clmgr/bin/cm node show -n master -M --display-no-header | awk '{print $3}')

# Run the performance validation script with pre-built Docker environments.
# This takes 1.5 hour to finish on a 32 GPU cluster.
docker run -it --name install-validation-tool --network host -v $(pwd):/pwd determinedai/install-validation-tool:0.17.14 create --output /pwd/result.json --cluster-gpus ${CLUSTER_GPUS} --node-gpus ${PER_NODE_GPUS} --master ${MASTER_ADDR} --data-dir /tmp --docker-registry determinedai

# Copy the result out and compare with reference.
docker run -it --name install-validation-tool-file-compare -v $(pwd):/pwd determinedai/install-validation-tool:0.17.14 file-compare --reference /pwd/mlds-32-gpu-reference.json --install /pwd/result.json
```

This will submit all performance validation experiments on the cluster, and provide details on any deviations that are found from the performance reference. It will print PASS or FAIL on the last line to indicate whether the performance of the cluster is validated.

A passed result looks like:

```bash
Comparing bert_checkpoint to reference...
OK: [bert_checkpoint, checkpoint_time]
Comparing bert_train_fs_with_pagecache to reference...
OK: [bert_train_fs_with_pagecache, cpu_util_simple]
OK: [bert_train_fs_with_pagecache, gpu_util]
OK: [bert_train_fs_with_pagecache, samples_per_second]

...

PASS: Reference comparison successful!
```

If it prints FAIL, run the following commands to save logs.

```bash
docker logs install-validation-tool &> install-validation-tool.log
docker logs install-validation-tool-file-compare &> install-validation-tool-file-compare.log
```

, and send the log file and the output file `result.json` to us.

If the performance tests fail on a mixed flavor of compute nodes, you might see outliers are detected in the performance validation tests. Please ignore the failures.

## Troubleshooting

1. If you hit the following issue:

```bash
[root@login ~]# docker run -it --name install-validation-tool-file-compare -v $(pwd):/pwd determinedai/install-validation-tool:0.17.14 file-compare --reference /pwd/mlds-32-gpu-reference.json --install /pwd/result.json
docker: Error response from daemon: Conflict. The container name "/install-validation-tool-file-compare" is already in use by container "b21d66af3fa1ba32cbfeef67f11c894a72feb11ac408c3ec89791e2617a23a8d". You have to remove (or rename) that container to be able to reuse that name.
See 'docker run --help'.
```

This means that you have already ocupy the container name with the previously started container. Run the following command to clean up:

```bash
docker rm -f install-validation-tool-file-compare
```