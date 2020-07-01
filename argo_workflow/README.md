# Using Determined + Argo for End to End Workflows
<p align="center">
<img src="https://github.com/determined-ai/determined/raw/master/determined-logo.png"></p>


This repository contains an example [Argo Workflow](https://github.com/argoproj/argo) that trains a model [using Determined](https://github.com/determined-ai/determined) and then deploys that model [using Seldon Core](https://github.com/SeldonIO/seldon-core).  Argo Workflows are an excellent tool for creating repeatable, scalable workflows in Kubernetes.


## Usage

### Prerequisites
Before running this example, you'll need a Kubernetes cluster with Seldon, Istio, and Argo installed.  One of the easiest ways to install all three is [via the Kubeflow project](https://github.com/kubeflow/kubeflow), however a standalone installation is certainly possible.  This example is built to work with a standard Kubeflow installation.

### Setup
For this example to work, you'll need to configure the Kubernetes `serviceaccount` used to be able to create seldon deployments and read istio services.  They'll probably look something like this:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: manage-seldon
  namespace: your-namespace
roleRef:
  kind: ClusterRole
  name: seldon-manager-role-kubeflow
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: default
  namespace: your-namespace
```

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-svc
  namespace: istio-system
roleRef:
  kind: ClusterRole
  name: istio-reader
  apiGroup: rbac.authorization.k8s.io
subjects:
- kind: ServiceAccount
  name: default
  namespace: your-namespace
```

### Running the Workflow
To run the workflow, simply run
```bash
argo submit -n your-namespace train_and_deploy.yaml --watch
```
