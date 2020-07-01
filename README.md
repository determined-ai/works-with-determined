# Example Determined Integrations

This repository compiles a series of example integrations between [Determined](https://github.com/determined-ai/determined) and other tools commonly used for machine learning workflows.  These code pieces are all meant to be examples of how you could use Determined with your existing tools.

## Data Tools

* [Pachyderm](pachyderm.com)
  * An example Pachyderm integration can be found [in the platform example](example_platform/README.md)
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
