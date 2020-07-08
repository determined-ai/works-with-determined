# Works With Determined

This repository highlights tools in the ML ecosystem that work well with [Determined](https://github.com/determined-ai/determined).  It contains working examples of  full end to end machine learning workflows that are enabled with the right sets of tools.

## Data Tools

* [Pachyderm](pachyderm.com)
  * An example Pachyderm integration can be found [in the platform example](example_platform/README.md)
* [DVC](dvc.org)
  * An example of using DVC to version data for Determined can be found [in the DVC example](dvc/README.md)
* [Delta Lake](delta.io)
  * An example of reading data from a Delta table to train a model in Determined can be found [in the spark example](spark_example/README.md)

## Serving Tools

* [Seldon Core](http://seldon.com/)
  * An example of using Seldon as a part of an end to end platform can be found [in the platform example](example_platform/README.md)
  * An example demonstrating automatic Seldon serving of models trained in Determined can be found [in the argo workflow example](argo_workflow/README.md)
* [Spark](https://spark.apache.org/)
  * An example that uses Spark to perform batch inference can be found [in the spark example](spark_ecosystem/README.md)

## Workflow Tools

* [Argo](https://argoproj.github.io/)
  * An example of using Determined within an Argo workflow to train a model then automatically deploy it with Seldon Core can be found [in the argo workflow example](argo_workflow/README.md)
* [Airflow](https://airflow.apache.org/)
  * An example of using Determined within an Airflow workflow to train a model then deploy it into Kubernetes with Seldon core can be found [in the airflow example](airflow/README.md)


## Platforms

* [Kubeflow](https://www.kubeflow.org/)
  * [The argo workflow example](argo_workflow/README.md) was specifically built to also be Kubeflow compatible, and can be uploaded and run as a [Kubeflow Pipeline](https://www.kubeflow.org/docs/pipelines/overview/pipelines-overview/)
