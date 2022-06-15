# Works With Determined

This repository highlights tools in the ML ecosystem that work well with [Determined](https://github.com/determined-ai/determined).  It contains working examples of  full end to end machine learning workflows that are enabled with the right sets of tools.

## Data Tools

* [Pachyderm](https://www.pachyderm.com)
  * An example Pachyderm integration can be found [in the Pachyderm-Seldon example](pachyderm-seldon/README.md)
* [DVC](https://www.dvc.org)
  * An example of using DVC to version data for Determined can be found [in the DVC example](dvc/README.md)
* [Delta Lake](https://www.delta.io)
  * An example of reading data from a Delta table to train a model in Determined can be found [in the spark example](spark_example/README.md)

## Serving Tools

* [Algorithmia](https://algorithmia.com/)
  * An example of using Determined with Algorithmia to train and deploy an Object Detection model can be found in the [Algorithmia example](/algorithmia/README.md)
* [Seldon Core](https://www.seldon.io/)
  * An example of using Seldon as a part of an end to end platform can be found [in the Pachyderm-Seldon example](pachyderm-seldon/README.md)
  * An example demonstrating automatic Seldon serving of models trained in Determined can be found [in the argo workflow example](kubeflow_pipelines/README.md)
* [Spark](https://spark.apache.org/)
  * An example that uses Spark to perform batch inference can be found [in the spark example](spark_ecosystem/README.md)

## Workflow Tools

* [Argo](https://argoproj.github.io/)
  * An example of using Determined within an Argo workflow to train a model then automatically deploy it with Seldon Core can be found [in the Kubeflow pipelines example](kubeflow_pipelines/README.md)
* [Airflow](https://airflow.apache.org/)
  * An example of using Determined within an Airflow workflow to train a model then deploy it into Kubernetes with Seldon core can be found [in the airflow example](airflow/README.md)

## Platforms

* [Kubeflow](https://www.kubeflow.org/)
  * [The Kubeflow pipelines example](kubeflow_pipelines/README.md) shows how to build a [Kubeflow Pipeline](https://www.kubeflow.org/docs/pipelines/overview/pipelines-overview/) with the Kubeflow Pipeline DSL that trains a model with Determined, saves improvements to the Determined model registry, then deploys that model with Seldon Core.

## ML Libraries

* [RAPIDS](https://rapids.ai/)
  * [The NVIDIA RAPIDS example](rapids/README.md) shows how to integrate RAPIDS into model training on Determined, in order to perform GPU-accelerated data loading and preprocessing.

## Observability Tools

* [Prometheus](https://prometheus.io)
  * [prometheus.yml](observability/prometheus/prometheus.yml) is a Prometheus configuration that works with the Prometheus endpoint that Determined surfaces to allow external observability tools to work with Determined
* [Grafana](https://grafana.com)
  * [Determined Hardware Dashboard](observability/grafana/determined-hardware-grafana.json) is a pre-configured Grafana dashboard that contains queries and panels that integrate with a Prometheus endpoint to visualize cluster usage metrics

## Cluster Managing Tool

* [HPCM](hpcm/README.md)

