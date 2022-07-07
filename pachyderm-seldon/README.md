# An example of an e2e MLOps pipeline 

This repository walks through an example of what an end-to-end MLOps pipeline could look like.  It uses all open source tools:

- [Pachyderm](https://www.pachyderm.com/) to manage, version and transform data
- [Determined](https://www.determined.ai) to train a model and manage model versions
- [Seldon](http://seldon.io/) to deploy models and request predictions

Actually, we will consider *Pachyderm Enterprise* and *Seldon Deploy* as there is some additional complexity that we want to cover and because these are the products normally found in production.

The overall integration will rely on the following Google Cloud infrastructure:

- All Pachyderm, Determined and Seldon components will be deployed on a GKE cluster
- Pachyderm will use a bucket to store the repositories
- Determined will use a bucket to store the models' checkpoints
- Seldon will use a bucket to store data for the model drift and outlier detectors
- Google Cloud Registry will be used to store the container images for the two Pachyderm's pipelines and the Seldon's serving image

In order to keep the explanation simple, let's break the integration description into a serie of steps:

- [General architecture](doc/architecture.md)
- [Software prerequisites](doc/prerequisites.md)
- [Environment setup](doc/environment.md)
- [Building the containers](doc/containers.md)
- [Examining the pipelines](doc/pipelines.md)
- Running use cases:
    - [Image classification](doc/image-classification.md)
    - [Market sentiment](doc/sentiment-analysis.md)
