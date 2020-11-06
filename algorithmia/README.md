# Object Detection with Determined and Algorithmia

## Pre-requisites
* AWS or GCP account and project if running in the cloud
* Algorithmia account


## Cluster Setup
Start a cluster using the Determined-Deploy (`det-deploy`) package.

```sh
pip install determined-deploy
```

Create the cluster in AWS, GCP, or on-premise. Refer to the official [Installation Guide](https://docs.determined.ai/latest/how-to/install-main.html). 

The following is an example command to start a cluster in GCP:

```sh
det-deploy gcp up --cluster-id <your_cluster_name> --project-id <your_gcp_project>
```

When the cluster is up, you will see the `MASTER_URL` returned, which can be pasted into your browser to access the Determined cluster.

## Notebook Setup

Determined supports running Jupyter notebooks on the cluster. Once your cluster is running, go to this repo and start a new notebook:

```sh
det -m <MASTER_URL> notebook start --config-file notebook.yaml -c .
```

The `--config-file` sets the configurations for the notebook and `-c` sets the context directory that should be uploaded to the cluster, in this case the current directory.


## Run the example

Once Jupyter Lab starts, open `Object-Detection-PyTorch-and-Algorithmia.ipynb` and run the example from the notebook.

*Note:* If running in the cloud, it may take a few minutes for a VM to be created before the notebook starts. When the notebook starts, it will automatically open in your browser.
