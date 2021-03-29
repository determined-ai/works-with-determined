# Determined & Metaflow

This repository outlines how Metaflow can be used to pre-process data, train a deep learning model on a Determined cluster, and retrieve the top checkpoint for local inference.

`example-determined.py` provides the template FlowSpec (DeterminedFLow), with steps to:
1. Preprocess and transform the data (placeholder)
2. Train the model on a Determined cluster
3. Retrieve the top checkpoint from the training and use it for local inference


## Run the Flow locally
Note: You'll need to have a Determined cluster set up locally. To do so, simply follow this `installation`<https://docs.determined.ai/latest/how-to/installation/deploy.html#install-determined-using-det-deploy> guide, which can be summarized as:
```commandline
pip(3) install determined-deploy
det-deploy local cluster-up <--no-gpu>
```

Once you have a Determined cluster running locally, you can proceed with:
1. `pip(3) install -r requirements`
2. `python(3) example-determined.py run --training-env local`

You can check the status of your local training job by going to the Determined WebUI, which defaults to:
http://localhost:8080


## Run the Flow on a non-local Cluster
Note: You'll need to have a non-local Determined cluster set up and the `master_url` of that cluster.

1. `pip(3) install -r requirements` # if you didn't run this previously
2. `python(3) example-determined.py run --training-env distributed --det-master <master_url>`

You can check the status of your distributed training job by going to the Determined WebUI for the cluster:
<master_url>:8080


## Use your best model for local inference
Now that you have a trained model, you can pull the best model checkpoint and use it for local inference with Metaflow's Notebook integration and Determined's Checkpoint API. Just open the `local_inference.ipynb` notebook by running:
```commandline
jupyter notebook
```

