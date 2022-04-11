# HPE ML Dev Sys Installation Guide

This guide provides steps for the installation teams to install the HPE ML Development Environment ("Environment") on the HPE ML Development System ("System") with HPCM. 

This guide assumes:

1. the installation team is familiar with general debugging skills on RHEL.
2. the installation team is familiar with HPCM.
3. the installation team knows what an HPE ML Dev Sys is.
4. an HPCM admin node is already installed with HPCM.

This installation guide supports the following versions:

| Supported Versions |
|--------------------|
| RHEL 8.5           |
| HPCM 1.7           |
| ML Dev Env 0.17.13 |

HPE ML Dev System contains four types of nodes:

- one HPCM admin node (HPCM management node on a DL325, the first node to be installed)
- one login service node (HPCM compute node on a DL325)
- one master service node (HPCM compute node on a DL325)
- multiple agent compute nodes (HPCM compute node on an Apollo 6500 with Nvidia A100 GPUs)

## Step 1 - Provisioning and Installing the HPCM Admin Node

This is the first node that needs to be installed before other nodes get installed. We assume that you can install this on your own.

## Step 2 - Provisioning the Login, Master, and Agent Nodes

Find the following HPCM OS image tar ball files in the installation package:

- `hpemlds-login-rhel8.5-0.17.13.tar.gz` for the login service node
- `hpemlds-master-rhel8.5-0.17.13.tar.gz` for the master service node
- `hpemlds-agent-gpu-rhel8.5-0.17.13.tar.gz` for the agent compute node with Nvidia GPUs and Infiniband

Assuming you are on the admin node, use the following commands to provision the nodes.

```bash
# Copy the tar ball files to the HPCM admin node

# Extract the tar file from the admin node where the file was transferred to:
tar -C /opt/clmgr/image/images --xattrs --acls --xattrs-include=* -zpxvf <image_name>.tar.gz

# Add the image to the HPCM
cm image create -i <image_name> --use-existing

# Provision the nodes.
cm node provision -i <image_name> -n <node_name>
```

## Step 3 - Configuring and Running the Master Node

Assuming you are on the master node, use the following commands to start the services.

```bash
# Start Docker Engine
systemctl start docker

# Run Postgres
docker run -d --restart unless-stopped --name hpe-mlde-db --network host -v determined_db:/var/lib/postgresql/data -e POSTGRES_DB=determined -e POSTGRES_PASSWORD=postgres postgres:10

# Create a configuration file master.yaml
# Note that this is a minimal setup without a checkpoint storage.
# Please update the bind_mounts and checkpoint_storage fields following the instruction in [Master Configuration](https://docs.determined.ai/0.17.13/sysadmin-basics/cluster-config.html#master-configuration) bind_mounts and checkpoint_storage if customers have customization for them.
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
  - pool_name: aux-pool
    max_aux_containers_per_agent: 100
EOF

# Run the Master
docker run -d --restart unless-stopped --name hpe-mlde-master --network host -v /etc/determined/master.yaml:/etc/determined/master.yaml determinedai/hpecaide-master:0.17.13
```

Run the following command to check if the services are running:

```bash
$ docker ps
CONTAINER ID   IMAGE                                  COMMAND                  CREATED          STATUS          PORTS     NAMES
797ba6a1eb3e   determinedai/hpecaide-master:0.17.13   "/usr/bin/determined…"   4 seconds ago    Up 3 seconds              hpe-mlde-master
c68d35ef0810   postgres:10                            "docker-entrypoint.s…"   12 seconds ago   Up 11 seconds             hpe-mlde-db
```

You should see similar results as above. The status should show `UP` for all the containers. If it shows other results such as `Restarted`, run the following commands to save the logs:

```bash
docker logs hpe-mlde-master &> hpe-mlde-master.log
docker logs hpe-mlde-db &> hpe-mlde-db.log
```

, and send the log files to us.

## Step 4 - Configuring and Running the Login Node

Assuming you are on the login node, use the following commands to start the services.

```bash
# Start Docker Engine
systemctl start docker

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
# Note that if customers need to configure proxy or TLS follow the instruction in [Agent Configuration](https://docs.determined.ai/0.17.13/sysadmin-basics/cluster-config.html#agent-configuration).
mkdir -p /etc/determined
cat << EOF > /etc/determined/agent.yaml
master_host: <master host>
master_port: <master port>
resource_pool: aux-pool
EOF

# Run the Agent
docker run -d --restart unless-stopped --name hpe-mlde-agent --network host -v /var/run/docker.sock:/var/run/docker.sock -v /etc/determined/agent.yaml:/etc/determined/agent.yaml determinedai/hpecaide-agent:0.17.13
```

Run the following command to check if the services are running:

```bash
$ docker ps
CONTAINER ID   IMAGE                                 COMMAND                  CREATED          STATUS                             PORTS                                       NAMES
d97dd9d6fa30   fluent/fluent-bit:1.6                 "/fluent-bit/bin/flu…"   1 second ago     Up 1 second                                                                    determined-fluent
dbd69a1c5ce6   determinedai/hpecaide-agent:0.17.13   "/run/determined/wor…"   2 seconds ago    Up 1 second                                                                    hpe-mlde-agent
cd2cbd8dea4f   gcr.io/cadvisor/cadvisor:v0.36.0      "/usr/bin/cadvisor -…"   27 seconds ago   Up 26 seconds (health: starting)   0.0.0.0:8080->8080/tcp, :::8080->8080/tcp   cadvisor
```

You should see similar results as above. The status should show `UP` for all the containers. If it shows other results such as `Restarted`, run the following commands to save the logs:

```bash
docker logs determined-fluent &> determined-fluent.log
docker logs hpe-mlde-agent &> hpe-mlde-agent.log
docker logs cadvisor &> cadvisor.log
```

, and send the log files to us.

## Step 5 - Configuring and Running Agent Compute Nodes on Apollo 6500

Assuming you are on the agent compute nodes, use the following commands to start the services.

```bash
# Start Docker Engine
systemctl start docker

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
# Note that if customers need to configure proxy or TLS follow the instruction in [Agent Configuration](https://docs.determined.ai/0.17.13/sysadmin-basics/cluster-config.html#agent-configuration).
mkdir -p /etc/determined
cat << EOF > /etc/determined/agent.yaml
master_host: <master host>
master_port: <master port>
resource_pool: compute-pool
EOF

# Run the Agent
docker run -d --restart unless-stopped --name hpe-mlde-agent --network host --gpus all -v /var/run/docker.sock:/var/run/docker.sock -v /etc/determined/agent.yaml:/etc/determined/agent.yaml determinedai/hpecaide-agent:0.17.13
```

Run the following command to check if the services are running:

```bash
$ docker ps
CONTAINER ID   IMAGE                                                      COMMAND                  CREATED          STATUS                             PORTS                                       NAMES
c250d9de3c5c   fluent/fluent-bit:1.6                                      "/fluent-bit/bin/flu…"   3 seconds ago    Up 2 seconds                                                                   determined-fluent
8a7eb011ea25   determinedai/hpecaide-agent:0.17.13                        "/run/determined/wor…"   4 seconds ago    Up 3 seconds                                                                   hpe-mlde-agent
97c18523930c   gcr.io/cadvisor/cadvisor:v0.36.0                           "/usr/bin/cadvisor -…"   26 seconds ago   Up 25 seconds (health: starting)   0.0.0.0:8080->8080/tcp, :::8080->8080/tcp   cadvisor
34eaa05d12fc   nvcr.io/nvidia/k8s/dcgm-exporter:2.3.2-2.6.3-ubuntu20.04   "/usr/local/dcgm/dcg…"   32 seconds ago   Up 31 seconds                      0.0.0.0:9400->9400/tcp, :::9400->9400/tcp   dgcm-exporter
```

You should see similar results as above. The status should show `UP` for all the containers. If it shows other results such as `Restarted`, run the following commands to save the logs:

```bash
docker logs determined-fluent &> determined-fluent.log
docker logs hpe-mlde-agent &> hpe-mlde-agent.log
docker logs cadvisor &> cadvisor.log
docker logs dgcm-exporter &> dgcm-exporter.log
```

, and send the log files to us.

## Step 6 - Check the overall installation

(Option 1) Go to the master web at `<master address:8080>`. You should be able to log in with the default username `determined` and an empty password. After click the cluster tab on the left navigation bar, you should be able to see two resource pools `compute-pool` and `aux-pool`:

- The compute pool should contain multiple connected agents depending on how many compute nodes are installed.
- The aux pool should contain only one connected agent.

See the image below:

<img width="1110" alt="HPE ML Dev Env Cluster Page" src="hpe-mlds-cluster-page.png">

(Option 2) Run the following command to check the installation:

```bash
$ curl <master-address>:8080/agents
```

Note that you need to check the `resource_pool` and `slots` fields to validate:

- The compute pool should contain multiple connected agents depending on how many compute nodes are installed.
- The aux pool should contain only one connected agent.

An example json looks like:

```json
{
  "/agents/5a5ec5a22303": {
    ...
    "slots": {
      "/agents/5a5ec5a22303/slots/0": {
        "id": "0",
        "device": {
          "id": 0,
          "brand": "Intel(R) Xeon(R) Gold 6126 CPU @ 2.60GHz x 48 cores",
          "uuid": "GenuineIntel",
          "type": "cpu"
        },
        "enabled": true,
        "container": null,
        "draining": false
      }
    },
    "resource_pool": "aux-pool",
    ...
  },
  "/agents/8a7eb011ea25": {
    ...
    "slots": {
      "/agents/8a7eb011ea25/slots/0": {
        "id": "0",
        "device": {
          "id": 0,
          "brand": "Tesla V100-SXM2-16GB",
          "uuid": "GPU-6800089c-a4ba-3e01-3d1f-f556326cedab",
          "type": "cuda"
        },
        "enabled": true,
        "container": null,
        "draining": false
      },
      ...
    },
    "resource_pool": "compute-pool",
    ...
  }
}
```

## Step 7 - Configuring and Running Monitoring Services on Admin Node

Note that because of the System's limited support for HPCM, some steps need to be done manually.

Find the following configuration files in the installation package:

- `hpe-mlds-prometheus-jobs.yaml` for the Prometheus jobs.
- `hpe-mlds-dashboard.json` for the Grafana dashboard json.

Assuming you are on the admin node, add Determined Prometheus jobs defined in [hpe-mlds-prometheus-jobs.yaml](hpe-mlds-prometheus-jobs.yaml) to be under the `scrape_configs` field in the configuration file `/etc/prometheus/prometheus.yml`. The result should look similar to:

```yaml
scrape_configs:
- job_name: det-master
  ...
- job_name: cadvisor-dcgm
  ...
```

Assuming you are on the admin node, run the following commands to start the services.

```bash
# Start the monitoring services
cm sim enable
cm sim start
```

Run the following command to check if the monitoring services are running.

```bash
$ cm sim status
Running is-active for prometheus service : prometheus.service 

admin: active

Running is-active for alertmanager service : alertmanager.service 

admin: active

Running is-active for core-services service: node_exporter.service 

admin: active

Running is-active for core-services service: process_exporter.service 

admin: active

Running is-active for monitoring-services service: mosquitto_exporter.service 

admin: active

Running is-active for monitoring-services service: logstash_exporter.service 

admin: active

Running is-active for monitoring-services service: postgres_exporter.service 

admin: active
```

Go to the web interface of the HPE ML Sys Grafana at `<admin-address>/grafana/dashboards`. You should be able to click into the dashboard tab on the left navi bar.
Add Determined Grafana Dashboard from [hpe-mlds-dashboard.json](hpe-mlds-dashboard.json) by using the dashboard importing button. The imported dashboard should look like the below image:

<img width="1110" alt="HPE ML Dev Env Grafana Page" src="hpe-mlds-grafana-page.png">
