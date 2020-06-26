# A Sample Deep Learning Platform

This repository walks through an example of what a "deep learning platform" could look like.  It uses
all open source tools:
- [Pachyderm](https://www.pachyderm.com/) to manage, version, and transform data
- [Determined](https://www.determined.ai) to train a model and manage model artifacts
- [Seldon Core](http://seldon.io/) to deploy models to Kubernetes

We walk through using this platform in [platform_example.ipynb](./platform_example.ipynb).


## Setup Instructions

These instructions will walk through installing Pachyderm, Determined, and Seldon.  This is a sample installation meant for a demo -- for an enterprise level installation you'll want to significantly customize this process.

### Prerequisites

- `kubectl`
- `eksctl`
- `helm`

### Creating your EKS Cluster
You can create your EKS cluster using `eksctl`.  The following command will work, but you'll want to customize `eks.yaml` to configure your cluster.  [See the eksctl documentation here.](https://eksctl.io/usage/creating-and-managing-clusters/)

```
eksctl create cluster -f cluster.yaml
```

### Installing Pachyderm on your cluster

Follow the Pachyderm docs to [deploy Pachyderm to your EKS cluster](https://docs.pachyderm.com/latest/deploy-manage/deploy/amazon_web_services/aws-deploy-pachyderm/).  You'll need to install `pachctl` as a part of this process

You'll want to expose the `pachd` process via s[ome sort of external IP address](https://docs.pachyderm.com/latest/deploy-manage/deploy/connect-to-cluster/#connect-by-using-a-pachyderm-context).  One way to do this (not recommended for production deployments) is to patch the `pachd` kubernetes service and make it a load balancer.  Something like:
```
kubectl patch svc pachd -p '{"spec": {"type": "LoadBalancer"}}'
```

### Installing Seldon Core on your cluster

Before installing Seldon Core, you'll want to install some sort of ingress provider.  One option is Ambassador, [which can be installed using helm](https://www.getambassador.io/docs/latest/topics/install/helm/).


You can then install Seldon Core with `helm` as well, [following their instructions](https://docs.seldon.io/projects/seldon-core/en/v1.1.0/workflow/install.html).

### Installing Determined

You can use [these instructions to create a Determined cluster in AWS.](https://docs.determined.ai/latest/how-to/installation/aws.html?highlight=aws).  Take note of the URL of the Determined Master, as you'll need it throughout this example.

## Setting up the Example
There are a few things you'll need to modify through the course of this example:

In [det/adaptive.yaml](det/adaptive.yaml), you'll need to update the pachyderm host field to the address of `pachd` that you set up above.

When you wrap your Docker image for use with Seldon, you'll need to push it to a docker registry, then update the image in
[seldon/serve.yaml](seldon/serve.yaml) with the docker image you pushed.

In the example notebook, you'll need to use the determined hostname, pachd hostname, and ambassador hostname, all of which you created while setting up your cluster.
