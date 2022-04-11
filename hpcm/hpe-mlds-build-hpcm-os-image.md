# Building HPE ML Dev Sys HPCM OS images Guide

This building guide supports the following versions:

| Supported Versions |
|--------------------|
| RHEL 8.5           |
| HPCM 1.7           |
| ML Dev Env 0.17.13 |

## Building HPE ML Dev Sys Master Node Image

This section follows [the guide for standard Determined installation with Docker](https://docs.determined.ai/latest/sysadmin-deploy-on-prem/docker.html) and [Configure Determined with Prometheus and Grafana](https://docs.determined.ai/latest/integrations/prometheus.html).

Note that all the HPCM images are based on RHEL 8.5.

### Installing Docker

Here follows [this instruction to install Docker on CentOS](https://docs.docker.com/engine/install/centos/#install-from-a-package).

```bash
# Install Docker
cm image dnf -i hpemldevsys-master --repos centos-8.5-docker,Red-Hat-Enterprise-Linux-8.5.0-x86_64 --duk install docker-ce docker-ce-cli containerd.io
```

### Pulling the Docker images for the Master

```bash
# Pull the Postgres Docker image
docker pull postgres:10

# Pull the Master Docker image
docker pull determinedai/hpecaide-master:0.17.13
```

### Baking OS images

```bash
cm image capture -i hpemlde-master-rhel8.5-0.17.13 -n <node name>
```

## Building HPE ML Dev Sys Compute Node Image

This section follows [the guide for standard Determined installation with Docker](https://docs.determined.ai/latest/sysadmin-deploy-on-prem/docker.html) and [Configure Determined with Prometheus and Grafana](https://docs.determined.ai/latest/integrations/prometheus.html).

Note that all the HPCM images are based on RHEL 8.5.

### Installing and Upgrading Nvidia Driver

- Installation and upgrading can be done by manually installing the [Nvidia runfile installer](https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html#runfile) on the compute nodes.
    - Walk through [the pre-installation steps](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#pre-installation-actions).
    - Installing the Nvidia driver using a package manager has many pain points as pointed out in [this page in HPCM wiki](https://hpedia.osp.hpe.com/wiki/HPCM/Cuda_Cross-Architecture_Chroot_Build).
- Install Nvidia driver (>=384.81) and prevent the kernel from loading automatically.

```bash
BASE_URL=https://us.download.nvidia.com/tesla
DRIVER_VERSION=510.47.03
curl -fSsl -O $BASE_URL/$DRIVER_VERSION/NVIDIA-Linux-x86_64-$DRIVER_VERSION.run
sh NVIDIA-Linux-x86_64-$DRIVER_VERSION.run

wget https://us.download.nvidia.com/tesla/510.47.03/nvidia-driver-local-repo-rhel8-510.47.03-1.0-1.x86_64.rpm
wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
cm repo add https://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/
```

### Installing Docker

Here follows [this instruction to install Docker on CentOS](https://docs.docker.com/engine/install/centos/#install-from-a-package).

```bash
# Install Docker
cm image dnf -i hpemldevsys-master --repos centos-8.5-docker,Red-Hat-Enterprise-Linux-8.5.0-x86_64 --duk install docker-ce docker-ce-cli containerd.io
```

### Installing the Nvidia Container Toolkit

- Follow [the official Nvidia Container Toolkit guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#installing-on-rhel-7)
    - Install it from `https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.repo`.

### Pulling the Docker images for the Compute Node

```bash
# Pull the DCGM-exporter
docker pull nvcr.io/nvidia/k8s/dcgm-exporter:2.3.2-2.6.3-ubuntu20.04

# Pull the cAdvisor
docker pull gcr.io/cadvisor/cadvisor:v0.36.0

# Pull the fluent-bit
docker pull fluent/fluent-bit:1.6

# Pull the default task environments
docker pull determinedai/environments:py-3.8-pytorch-1.9-lightning-1.5-tf-2.4-cpu-0.17.10
docker pull determinedai/environments:cuda-11.1-pytorch-1.9-lightning-1.5-tf-2.4-gpu-0.17.10

# Pull the Agent Docker image
docker pull determinedai/hpecaide-agent:0.17.13
```

### Baking OS images

```bash
cm image capture -i hpemlde-agent-gpu-rhel8.5-0.17.13 -n <node name>
```

## Building HPE ML Dev Sys Login Node Image

This section follows [the guide for standard Determined installation with Docker](https://docs.determined.ai/latest/sysadmin-deploy-on-prem/docker.html) and [Configure Determined with Prometheus and Grafana](https://docs.determined.ai/latest/integrations/prometheus.html).

Note that all the HPCM images are based on RHEL 8.5.

### Installing Docker

Here follows [this instruction to install Docker on CentOS](https://docs.docker.com/engine/install/centos/#install-from-a-package).

```bash
# Install Docker
cm image dnf -i hpemldevsys-master --repos centos-8.5-docker,Red-Hat-Enterprise-Linux-8.5.0-x86_64 --duk install docker-ce docker-ce-cli containerd.io
```

### Pulling the Docker images for the Login Node

```bash
# Pull the Docker Registry Server
docker pull registry:2.8

# Pull the cAdvisor
docker pull gcr.io/cadvisor/cadvisor:v0.36.0

# Pull the fluent-bit
docker pull fluent/fluent-bit:1.6

# Pull the default task environments
docker pull determinedai/environments:py-3.8-pytorch-1.9-lightning-1.5-tf-2.4-cpu-0.17.10

# Pull the Agent Docker image
docker pull determinedai/hpecaide-agent:0.17.13
```

### Baking OS images

```bash
# Capture the HPCM OS image from a node
cm image capture -i hpemlde-agent-gpu-rhel8.5-0.17.13 -n <node name>

# Save the HPCM OS image in a tar ball file
tar -C /opt/clmgr/image/images --numeric-owner --xattrs --acls -cpvzf <image_name>.tar.gz <image_name>
```