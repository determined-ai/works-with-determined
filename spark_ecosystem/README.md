# Determined Spark Summit 2020 Demo
<p align="center">
<img src="https://github.com/determined-ai/determined/raw/master/determined-logo.png"></p>

This repository implements an integration between [Determined](http://determined.ai), [Delta Lake](https://delta.io/), and [Apache Spark](https://spark.apache.org/).  Specifically, it:
* Performs ETL using Spark to transform raw data into a Delta table
* Provides [a Delta connector](data.py) allowing Determined to read from a versioned Delta table.
* Trains a model using the Determined training platform
* Programmatically exports checkpoints from Determined to Spark for batch inference

## Setup

This example was run on [Amazon EMR](https://aws.amazon.com/emr/).  As a few additional steps setting up this EMR cluster, invoke [this provided shell script](emr/emr-startup.sh) as a bootstrap action when setting up the cluster.  

## Running

For ETL, [voc_to_delta.ipynb](spark/voc_to_delta.ipynb) provides the code to land the Pascal VOC dataset into a Delta table.  Note that it is hard coded to the default VOC  directory structure.

The Determined experiments can be created from [determined.ipynb](determined.ipynb), or from the CLI.  Be sure to update [your experiment config](search.yaml) such that it points to your Delta table.

Inference is done in [batch_inference.ipynb](spark/batch_inference.ipynb).  Predictions are also written as a Delta table.

## Need Help?

If you have any questions or need any help, please join the [Determined Community Slack](https://join.slack.com/t/determined-community/shared_invite/zt-cnj7802v-KcVbaUrIzQOwmkmY7gP0Ew), we'd be happy to help out!
