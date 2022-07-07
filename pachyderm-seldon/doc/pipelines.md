# Examining the pipelines

Pipelines are heavily dependant on the use case so each use case will have its own pipelines and we have put them just inside the use case's folder. We will describe the `training` and `development` pipelines for the image classification use case, which are located in `pachyderm-seldon/use-case/image-classification`.

As these pipelines have been already described in terms of functionality, here we will focus on their configuration.

## The training pipeline

The training pipeline takes care of running [re]training experiments and creating models. It is shown below and the important aspects to consider are:

 - the `pipeline's name`: this is important as the name of this pipeline will be used by Pachyderm to create its output repository, which will be the input repo for the deployment pipeline 
 - the `pipeline's input`: this pipeline takes its input directly from the *dogs-and-cats* repo
 - the `container image`: this is our training image and is independant on the use case/experiment
 - the `script's parameters`: these parameters drive the training process. We can see experiment information (its GitHub repo and the location inside it, the configuration to use), the Pachyderm's input repo with datafiles and the output model to create
 - the `environmental variables`: some infrastructure parameters are stored into secrets and are provided to the pipeline through the use of environmental variables. These values are independant on the use case

```
{
  "pipeline": {
    "name": "dogs-and-cats-model"
  },
  "input": {
    "pfs": {
      "name": "data",
      "repo": "dogs-and-cats",
      "branch": "master",
      "glob": "/",
      "empty_files": true
    }
  },
  "transform": {
    "cmd": ["/bin/sh"],
    "stdin": ["python train.py --git-url https://git@github.com:/determined-ai/works-with-determined.git --git-ref master --sub-dir pachyderm-seldon/use-case/image-classification/experiment --config const.yaml --repo dogs-and-cats --model dogs-and-cats"],
    "image": "gcr.io/determined-ai/pachyderm-seldon/train:0.0.19",
    "secrets": [
      {
        "name": "pipeline-secret",
        "key": "det_master",
        "env_var": "DET_MASTER"
      },
      {
        "name": "pipeline-secret",
        "key": "det_user",
        "env_var": "DET_USER"
      },
      {
        "name": "pipeline-secret",
        "key": "det_password",
        "env_var": "DET_PASSWORD"
      },
      {
        "name": "pipeline-secret",
        "key": "pac_token",
        "env_var": "PAC_TOKEN"
      }
    ]
  }
}
```


## The deployment pipeline

The deployment pipeline takes care of creating a deployment on Seldon in order to serve predictions and is shown below. Like the previous pipeline, there are some important aspects to consider:

 - the `pipeline's input`: the name of the input repo is *dogs-and-cats-model*, meaning that this pipeline is taking its input from the training pipeline
 - the `container image`: this is our deployment image and is independant on the use case/experiment
 - the `script's parameters`: these parameters drive the deployment process. We can see the name of the deployment to create, the serving image to use and a few parameters for the drift and outlier detectors. Some parameters, like the model name and version to serve, are taken directly from the input repository
 - the `environmental variables`: same as for the training pipeline, with the values independant on the use case

```
{
  "pipeline": {
    "name": "dogs-and-cats-deploy"
  },
  "input": {
    "pfs": {
      "name": "data",
      "repo": "dogs-and-cats-model",
      "branch": "master",
      "glob": "/"
    }
  },
  "transform": {
    "cmd": ["/bin/sh"],
    "stdin": ["python deploy.py --deploy-name dogcat-deploy --detect-bucket-uri gs://determined-seldon-detector --detect-batch-size 4 --serving-image gcr.io/determined-ai/pachyderm-seldon/serve:0.0.6"],
    "image": "gcr.io/determined-ai/pachyderm-seldon/deploy:0.0.7",
    "secrets": [ 
      {
        "name": "pipeline-secret",
        "key": "det_master",
        "env_var": "DET_MASTER"
      },
      {
        "name": "pipeline-secret",
        "key": "det_user",
        "env_var": "DET_USER"
      },
      {
        "name": "pipeline-secret",
        "key": "det_password",
        "env_var": "DET_PASSWORD"
      },
      {
        "name": "pipeline-secret",
        "key": "sel_url",
        "env_var": "SEL_URL"
      },
      {
        "name": "pipeline-secret",
        "key": "sel_secret",
        "env_var": "SEL_SECRET"
      },
      {
        "name": "pipeline-secret",
        "key": "sel_namespace",
        "env_var": "SEL_NAMESPACE"
      }
    ]
  }
}
```

---
[Up](../README.md) | [Next](image-classification.md)
 
