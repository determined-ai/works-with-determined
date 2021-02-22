# Speedy Tabular Learning with Determined and NVIDIA RAPIDS

## Prerequisites
* [Determined cluster](https://docs.determined.ai/latest/how-to/install-main.html) with NVIDIA Pascal or later GPUs attached to agents.
* [Determined CLI](https://docs.determined.ai/latest/how-to/install-cli.html) installed and configured to submit workloads to the cluster.

## Running the examples

The following experiment uses RAPIDS cuDF to load and preprocess data, to then train a sales prediction [TabNet](https://arxiv.org/abs/1908.07442) model in Determined: 

```sh
cd experiment/
det e create cudf.yaml .
```

This second experiment uses Pandas instead of cuDF to load and preprocess data, and holds everything else the same as the experiment above.  This highlights the performance benefits and API friendliness of RAPIDS and demonstrates how easy it is to integrate RAPIDS into Determined workflows:
 

```sh
det e create pandas.yaml .
```

## Environment setup

The experiments above are configured to use an existing image. In order to integrate RAPIDS in your own Determined images, follow the [custom image](https://docs.determined.ai/latest/how-to/custom-env.html#custom-images) pattern [here](environment).
