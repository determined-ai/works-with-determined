# HPE ML Dev Sys Performance Validation Guide

This guide provides steps for the installation teams to validate the performance of HPE ML Development System ("System").

This guide assumes:

1. the installation team is familiar with general debugging skills on RHEL.
2. the installation team is familiar with HPCM.
3. the installation team knows what an HPE ML Dev Sys is.
4. the System is already installed with SW.

This performance validation guide supports the following versions:

| Supported Versions |
|--------------------|
| RHEL 8.5           |
| HPCM 1.7           |
| ML Dev Env 0.17.11 |

## Step 1 - Ensuring the Master is Running

Before running the performance validation script, ensure that the master is running. You should also check if the resource pools have the correct number of connected agents.

## Step 2 - Transferring Performance Validation Task Environment to Agent Nodes 

Find the following performance validation task environment Docker image tar ball files in the installation package:

- `hpemlds-docker-install-validation-mmdetection-0.17.11.tar`
- `hpemlds-docker-install-validation-transformers-0.17.11.tar`

Copy the tar ball files to all agent compute nodes on Apollo 6500.

Assume you are on the agent compute nodes, use the following commands to load Docker images from those tar ball files.

```bash
docker load -i hpemlds-docker-install-validation-mmdetection-0.17.11.tar
docker load -i hpemlds-docker-install-validation-transformers-0.17.11.tar
```

Run the following commands to check if the images are loaded:

```bash
$ docker images
REPOSITORY                                     TAG                                                       IMAGE ID            CREATED             SIZE
determinedai/hpecaide-agent                    0.17.13                                                   4afe089f8dcf        2 days ago          98.6MB
determinedai/install-validation-transformers   0.17.11                                                   6739bbb639d1        2 weeks ago         24.8GB
determinedai/install-validation-mmdetection    0.17.11                                                   df9f8d07aae3        2 weeks ago         25.1GB
determinedai/environments                      cuda-11.3-pytorch-1.10-lightning-1.5-tf-2.8-gpu-0.17.12   2647c83f896e        3 weeks ago         15.9GB
determinedai/environments                      cuda-11.3-pytorch-1.10-lightning-1.5-tf-2.8-gpu-83dbcaa   2647c83f896e        3 weeks ago         15.9GB
nvcr.io/nvidia/k8s/dcgm-exporter               2.3.2-2.6.3-ubuntu20.04                                   009d8c29385c        2 months ago        570MB
fluent/fluent-bit                              1.6                                                       672c60a7ab2a        15 months ago       78.3MB
nvidia/cuda                                    11.0-base                                                 2ec708416bb8        20 months ago       122MB
gcr.io/cadvisor/cadvisor                       v0.36.0                                                   7414b6ed960c        22 months ago       184MB
```

You should see similar results as above. The images should include `determinedai/install-validation-transformers:0.17.11` and `determinedai/install-validation-mmdetection:0.17.11`

## Step 3 - Submitting Performance Validation Jobs on Login Node

Assuming you are on the login node, use the following commands to submit performance validation jobs:

```bash
# Start Docker Engine
systemctl start docker

# Run the performance validation script with pre-built Docker environments.
# Replace <NUM_GPU> with the number of GPUs on the cluster. The number of GPUs
# can be calculated by using 8 * <NUM_AGENT_COMPUTE_NODES>
docker run -it --rm --name install_validation_tool --network host -v $(pwd):/install_validation_tool/pwd determinedai/install-validation-tool:0.17.11 compare --reference /install_validation_tool/pwd/mlds-<NUM_GPU>-gpu-reference.json --output /install_validation_tool/pwd/mlds-<NUM_GPU>-gpu-compare.json --num-gpus <NUM_GPU> --data-dir /tmp --docker-registry determinedai
```

This will submit all performance validation experiments on the cluster, and provide details on any deviations that are found from the performance reference. It will print PASS or FAIL on the last line to indicate whether the performance of the cluster is validated. 

If it prints FAIL, run the following commands to save logs.

```bash
docker logs install-validation-tool &> install-validation-tool.log
```

, and send the log file and the output file `mlds-<NUM_GPU>-gpu-compare.json` to us.