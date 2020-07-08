# Using Determined and DVC for Data Versioning
<p align="center">
<img src="https://github.com/determined-ai/determined/raw/master/determined-logo.png"></p>

This repository contains an example integration between [Determined](https://github.com/determined-ai/determined) and [DVC](https://github.com/iterative/dvc), using DVC to manage data versions.

This specific example works with the [Asirra Dogs vs. Cats Dataset](https://www.kaggle.com/c/dogs-vs-cats/data) to create an image classification model.

## Prerequisites
* Download the [Asirra Dogs vs. Cats Dataset](https://www.kaggle.com/c/dogs-vs-cats/data) and extract it into the `images` directory.
  * Manually create a train / evaluation split, placing the training images in `images/train/` and the evaluation images in `images/eval/`
* [Install DVC](https://dvc.org/doc/install)

## Setup
Set up DVC to version your dataset:
```
dvc init
dvc add images/
```

Configure remote storage for your data.  You'll need to make sure your Determined agents can access this remote location (with IAM roles for example)
```
dvc remote add -d storage s3://<YOUR-S3-BUCKET>/cat-dog-dataset
```
And push the local data to remote storage:
```
dvc push
```

## How it Works
To submit a Determined experiment, use:
```
det e create train.yaml .
```

In the [startup hook](startup-hook.sh), we use DVC to pull the current version of the dataset (as defined locally).  This works seamlessly, as the Determined CLI automatically uploads the current DVC configuration to Determined.
