# Building HPE ML Dev Sys HPCM OS images Guide

This building guide supports the following versions:

| Supported Versions |
|--------------------|
| RHEL 8.5           |
| HPCM 1.7           |
| ML Dev Env 0.17.15 |

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
docker pull determinedai/hpe-mlde-master:0.17.15
```

### Configuring and Running the Master Service

Write the following file into `/root/hpe-mlde-master-start.sh`.

```bash
#!/bin/bash

# Enable and start Docker Engine
systemctl enable docker
systemctl enable containerd
systemctl start docker
systemctl start containerd

# Run Postgres
docker run -d --restart unless-stopped --name hpe-mlde-db --network host -v determined_db:/var/lib/postgresql/data -e POSTGRES_DB=determined -e POSTGRES_PASSWORD=postgres postgres:10

# Create a configuration file master.yaml
# Note that this is a minimal setup without a checkpoint storage.
# Please update the bind_mounts and checkpoint_storage fields following the instruction in [Master Configuration](https://docs.determined.ai/0.17.15/sysadmin-basics/cluster-config.html#master-configuration) bind_mounts and checkpoint_storage if customers have customization for them.
mkdir -p /etc/determined
cat << EOF > /etc/determined/master.yaml
port: 8080

db:
  user: postgres
  host: 127.0.0.1
  port: 5432
  name: determined
  password: postgres

checkpoint_storage:
  type: shared_fs
  host_path: /tmp
  storage_path: determined-checkpoint
  save_experiment_best: 0
  save_trial_best: 1
  save_trial_latest: 1

observability:
  enable_prometheus: true

resource_manager:
  type: agent
  default_compute_resource_pool: compute-pool
  default_aux_resource_pool: aux-pool

resource_pools:
  - pool_name: compute-pool
    max_aux_containers_per_agent: 0
    task_container_defaults:
      shm_size_bytes: 137438953472
      dtrain_network_interface: ib0
      add_capabilities:
        - IPC_LOCK
      devices:
        - host_path: /dev/infiniband/
          container_path: /dev/infiniband/
  - pool_name: aux-pool
    max_aux_containers_per_agent: 100
EOF
echo "### PRINT MASTER CONFIG START"
cat /etc/determined/master.yaml
echo "### PRINT MASTER CONFIG END"

# Run the Master
docker run -d --restart unless-stopped --name hpe-mlde-master --network host -v /etc/determined/master.yaml:/etc/determined/master.yaml determinedai/hpe-mlde-master:0.17.15
```

And run:

```bash
chmod 700 /root/hpe-mlde-master-start.sh
```

### Baking OS images

```bash
# Clean the history
docker rm -f hpe-mlde-master  hpe-mlde-db
rm -rf /etc/determined/
rm -f ~/.bash_history 
history -c

# Capture the HPCM OS image from a node
cm image capture -i hpe-mlde-master-0.17.15-rhel-8.5 -n <node name>

# Save the HPCM OS image in a tar ball file
tar -C /opt/clmgr/image/images --numeric-owner --xattrs --acls -cpvzf hpe-mlde-master-0.17.15-rhel-8.5.tar.gz hpe-mlde-master-0.17.15-rhel-8.5
```


## Building HPE ML Dev Sys Login Node Image

This section follows [the guide for standard Determined installation with Docker](https://docs.determined.ai/latest/sysadmin-deploy-on-prem/docker.html) and [Configure Determined with Prometheus and Grafana](https://docs.determined.ai/latest/integrations/prometheus.html).

Note that all the HPCM images are based on RHEL 8.5.

### Installing Docker

Here follows [this instruction to install Docker on CentOS](https://docs.docker.com/engine/install/centos/#install-from-a-package).

```bash
# Install Docker
cm image dnf -i hpe-mlde-agent --repos centos-8.5-docker,Red-Hat-Enterprise-Linux-8.5.0-x86_64 --duk install docker-ce docker-ce-cli containerd.io
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
docker pull determinedai/environments:py-3.8-pytorch-1.10-lightning-1.5-tf-2.8-cpu-ed66d8a

# Pull the Agent Docker image
docker pull determinedai/hpe-mlde-agent:0.17.15

# Pull the install validation tool
docker pull determinedai/install-validation-tool:0.17.14
```

### Configuring and Running the Login Service

Write the following file into `/root/hpe-mlde-login-start.sh`.

```bash 
#!/bin/bash

# Enable and start Docker Engine
systemctl enable docker
systemctl enable containerd
systemctl start docker
systemctl start containerd

# Run cAdvisor on 8080
docker run -d --restart unless-stopped --name cadvisor \
  --volume /:/rootfs:ro \
  --volume /var/run:/var/run:ro \
  --volume /sys:/sys:ro \
  --volume /var/lib/docker/:/var/lib/docker:ro \
  --volume /dev/disk/:/dev/disk:ro \
  --publish 8080:8080 \
  --privileged \
  --device /dev/kmsg \
  gcr.io/cadvisor/cadvisor:v0.36.0

# Create an agent configuration file.
# Replace the placeholder with actual values.
# Note that if customers need to configure proxy or TLS follow the instruction in [Agent Configuration](https://docs.determined.ai/0.17.15/sysadmin-basics/cluster-config.html#agent-configuration).
mkdir -p /etc/determined
cat << EOF > /etc/determined/agent.yaml
master_host: $(/opt/clmgr/bin/cm node show -n master -M --display-no-header | awk '{print $3}')
master_port: 8080
resource_pool: aux-pool
EOF
echo "### PRINT AGENT CONFIG START"
cat /etc/determined/agent.yaml
echo "### PRINT AGENT CONFIG END"

# Run the Agent
docker run -d --restart unless-stopped --name hpe-mlde-agent --network host -v /var/run/docker.sock:/var/run/docker.sock -v /etc/determined/agent.yaml:/etc/determined/agent.yaml determinedai/hpe-mlde-agent:0.17.15
```

And run:

```bash
chmod 700 /root/hpe-mlde-login-start.sh
```

### Baking OS images

```bash
# Clean the history
docker rm -f determined-fluent hpe-mlde-agent cadvisor
rm -rf /etc/determined/
rm -f ~/.bash_history 
history -c

# Capture the HPCM OS image from a node
cm image capture -i hpe-mlde-login-0.17.15-rhel-8.5 -n <node name>

# Save the HPCM OS image in a tar ball file
tar -C /opt/clmgr/image/images --numeric-owner --xattrs --acls -cpvzf hpe-mlde-login-0.17.15-rhel-8.5.tar.gz hpe-mlde-login-0.17.15-rhel-8.5
```

## Building HPE ML Dev Sys Nvidia Agent Node Image for Apollo 6500 with Nvidia GPUs

This section follows [the guide for standard Determined installation with Docker](https://docs.determined.ai/latest/sysadmin-deploy-on-prem/docker.html) and [Configure Determined with Prometheus and Grafana](https://docs.determined.ai/latest/integrations/prometheus.html).

Note that all the HPCM images are based on RHEL 8.5.

### Installing the drivers

Download the drivers with the following commands:

```bash
# Nvidia Driver
BASE_URL=https://us.download.nvidia.com/tesla
DRIVER_VERSION=510.47.03
curl -fSsl -O $BASE_URL/$DRIVER_VERSION/NVIDIA-Linux-x86_64-$DRIVER_VERSION.run

# Nvidia CUDA
wget https://developer.download.nvidia.com/compute/cuda/11.6.2/local_installers/cuda_11.6.2_510.47.03_linux.run

# Mellanox OFED

```

Install with the following commands:

```bash
# GCC
cm node dnf -n <> install gcc gcc-gfortran tk kernel-modules-extra

# MLNX OFED
## See https://docs.nvidia.com/networking/display/MLNXOFEDv551032/Installing+MLNX_OFED
tar -xzvf MLNX_OFED_LINUX-5.5-1.0.3.2-rhel8.5-x86_64.tar.gz
cd MLNX_OFED_LINUX-5.5-1.0.3.2-rhel8.5-x86_64
mount -o ro,loop MLNX_OFED_LINUX-5.5-1.0.3.2-rhel8.5-x86_64.iso /mnt
## --force specify uninstallation of conflict libraries.
## firmware is already installed with iLo.
cd /mnt
./mlnxofedinstall --force --without-fw-update
modprobe -rv rpcrdma ib_srpt ib_isert
/etc/init.d/openibd restart

# Nvidia Driver
## Pre-installation steps:
## https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html#pre-installation-actions
## This should install the fabric manager and peer memory automatically.
sh NVIDIA-Linux-x86_64-$DRIVER_VERSION.run

## Enable nvidia peer memory
## https://download.nvidia.com/XFree86/Linux-x86_64/510.47.03/README/nvidia-peermem.html
modprobe nvidia-peermem
echo "nvidia-peermem" | sudo tee /etc/modules-load.d/nvidia-peermem.conf

## Check installation
nvidia-smi
nvidia-smi nvlink -s
lsmod | grep -E '(nvidia_peermem)'
hca_self_test.ofed
```

### Installing Docker

Here follows [this instruction to install Docker on CentOS](https://docs.docker.com/engine/install/centos/#install-from-a-package).

```bash
# Install Docker
cm image dnf -i hpe-mlde-master --repos centos-8.5-docker,Red-Hat-Enterprise-Linux-8.5.0-x86_64 --duk install docker-ce docker-ce-cli containerd.io
```

### Installing the Nvidia Container Toolkit

- Follow [the official Nvidia Container Toolkit guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#installing-on-rhel-7)
    - Install it from `https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.repo`.

### Create Nvidia Persistence Daemon

```bash
cat << EOF > /usr/lib/systemd/system/nvidia-persistenced.service
[Unit]
Description=NVIDIA Persistence Daemon
Before=docker.service
Wants=syslog.target

[Service]
Type=forking
PIDFile=/var/run/nvidia-persistenced/nvidia-persistenced.pid
Restart=always
ExecStart=/usr/bin/nvidia-persistenced --verbose
ExecStopPost=/bin/rm -rf /var/run/nvidia-persistenced

[Install]
WantedBy=multi-user.target
EOF
```

### Pulling the Docker images for the Compute Node

```bash
# Pull the DCGM-exporter
docker pull nvcr.io/nvidia/k8s/dcgm-exporter:2.3.2-2.6.3-ubuntu20.04

# Pull the cAdvisor
docker pull gcr.io/cadvisor/cadvisor:v0.36.0

# Pull the fluent-bit
docker pull fluent/fluent-bit:1.6

# Pull the default task environments
docker pull determinedai/environments:py-3.8-pytorch-1.10-lightning-1.5-tf-2.8-cpu-ed66d8a
docker pull determinedai/environments:cuda-11.3-pytorch-1.10-lightning-1.5-tf-2.8-gpu-ed66d8a

# Pull the Agent Docker image
docker pull determinedai/hpe-mlde-agent:0.17.15
```

## Configuring and Running Agent Compute Nodes on Apollo 6500

Write the following file into `/root/hpe-mlde-agent-cuda-start.sh`.

```bash
#!/bin/bash

# Enable and start Docker Engine
systemctl enable nvidia-persistenced nvidia-fabricmanager docker containerd
systemctl start nvidia-persistenced nvidia-fabricmanager docker containerd

# Load nvidia-peermem
modprobe nvidia-peermem

# Run dcgm-exporter on port 9400 for agents with GPUs
docker run -d --restart unless-stopped --name dgcm-exporter --gpus all -p 9400:9400 nvcr.io/nvidia/k8s/dcgm-exporter:2.3.2-2.6.3-ubuntu20.04

# Run cAdvisor on 8080
docker run -d --restart unless-stopped --name cadvisor \
  --volume /:/rootfs:ro \
  --volume /var/run:/var/run:ro \
  --volume /sys:/sys:ro \
  --volume /var/lib/docker/:/var/lib/docker:ro \
  --volume /dev/disk/:/dev/disk:ro \
  --publish 8080:8080 \
  --privileged \
  --device /dev/kmsg \
  gcr.io/cadvisor/cadvisor:v0.36.0

# Create an agent configuration file.
# Replace the placeholder with actual values.
# Note that if customers need to configure proxy or TLS follow the instruction in [Agent Configuration](https://docs.determined.ai/0.17.15/sysadmin-basics/cluster-config.html#agent-configuration).
mkdir -p /etc/determined
cat << EOF > /etc/determined/agent.yaml
master_host: $(/opt/clmgr/bin/cm node show -n master -M --display-no-header | awk '{print $3}')
master_port: 8080
resource_pool: compute-pool
EOF
echo "### PRINT AGENT CONFIG START"
cat /etc/determined/agent.yaml
echo "### PRINT AGENT CONFIG END"

# Run the Agent
docker run -d --restart unless-stopped --name hpe-mlde-agent --network host --gpus all -v /var/run/docker.sock:/var/run/docker.sock -v /etc/determined/agent.yaml:/etc/determined/agent.yaml determinedai/hpe-mlde-agent:0.17.15
```

And run:

```bash
chmod 700 /root/hpe-mlde-agent-cuda-start.sh
```

### Baking OS images

```bash
# Clean the history
docker rm -f hpe-mlde-agent cadvisor dgcm-exporter
rm -rf /etc/determined/
rm -f ~/.bash_history 
history -c

# Capture the HPCM OS image from a node
cm image capture -i hpe-mlde-agent-cuda-0.17.15-rhel-8.5 -n <node name>

# Save the HPCM OS image in a tar ball file
tar -C /opt/clmgr/image/images --numeric-owner --xattrs --acls -cpvzf hpe-mlde-agent-cuda-0.17.15-rhel-8.5.tar.gz hpe-mlde-agent-cuda-0.17.15-rhel-8.5
```
