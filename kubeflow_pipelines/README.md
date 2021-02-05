# Using Determined + Kubeflow Pipelines
<p align="center">
<img src="https://github.com/determined-ai/determined/raw/master/determined-logo.png"></p>


This repository contains an example [Kubeflow Pipeline](https://www.kubeflow.org/docs/pipelines/overview/pipelines-overview/) that trains a model [using Determined](https://github.com/determined-ai/determined), versions that model using the Determined model registry, then deploys that model [using Seldon Core](https://github.com/SeldonIO/seldon-core).  Kubeflow pipelines are excellent ways to create repeatable, scalable workflows in Kubernetes -- perfect for things like retraining pipelines for deep learning.

<img src="resources/pipeline_screenshot.png"></p>


## Usage

### Prerequisites
Before running this example, you'll need a Kubernetes cluster with [Kubeflow installed](https://github.com/kubeflow/kubeflow).

### Setup
For this example to work, you'll need to:
 1. ensure the Kubernetes cluster has access to wherever your Determined checkpoints are stored. For example, if deploying Kubernetes with EKS and using S3 for checkpoints, you'll want to make sure the service account for your AWS Node-Group has access to the same S3 bucket where you store your Determined checkpoints. You can add this permission in AWS using the following, replacing `bucket-name` with the actual name of your S3 bucket:
 
    ```yaml
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::bucket-name"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:DeleteObject"
                ],
                "Resource": [
                    "arn:aws:s3:::bucket-name/*"
                ]
            }
        ]
    }
    ```
 2. Create a new namespace in Kubernetes where you'd like to deploy Seldon. Going forward we'll refer to this namespace as `<NEW_NAMESPACE>`.
 
 3. Configure the Kubernetes `serviceaccount` used to be able to create seldon deployments and read istio services.  You can apply the following to the service account, replacing `<NEW_NAMESPACE>` with the Kubernetes namespace created above, and `<KF_USER_NAMESPACE>` with the namespace created when you first started Kubeflow and logged in.

    To apply these updates, run `kubectl apply -f <file>.yaml` where `<file>` is the file created from these configurations. 
        
    ```yaml
    apiVersion: rbac.authorization.k8s.io/v1
    kind: RoleBinding
    metadata:
      name: manage-seldon
      namespace: <NEW_NAMESPACE>
    roleRef:
      kind: ClusterRole
      name: seldon-manager-role-kubeflow
      apiGroup: rbac.authorization.k8s.io
    subjects:
    - kind: ServiceAccount
      name: default-editor
      namespace: <KF_USER_NAMESPACE>
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
      name: default-editor
      namespace: <KF_USER_NAMESPACE>
    ```

 4. If you're using using an Istio gateway, ensure it is set as a Load Balancer:
    ```
    kubectl patch svc istio-ingressgateway -n istio-system -p '{"spec":{"type":"LoadBalancer"}}'
    ```

 5. Build and upload the Seldon docker image using the Dockerfile in the Seldon subdirectory. Ensure this image is accessible by your Kubernetes cluster.

### Upload the Kubeflow Pipeline

Upload `train_and_deploy.yaml` via the Kubeflow Pipelines UI. When you create a new run, you'll need to update the variables for:
* Determined master: IP or URL of your Determined master
* Deployment namespace: `<NEW_NAMESPACE>`
* Image: the Seldon docker image you previously built
