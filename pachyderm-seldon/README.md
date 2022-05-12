# An example of a Deep Learning platform 

This repository walks through an example of what a "deep learning platform" could look like.  It uses all open source tools:

- [Pachyderm](https://www.pachyderm.com/) to manage, version and transform data
- [Determined](https://www.determined.ai) to train a model and manage model artifacts
- [Seldon Core](http://seldon.io/) to deploy models and request predictions

The architecture of the platform will be the following one:

- All Pachyderm, Determined and Seldon components will be deployed on a GKE cluster on Google Cloud
- Pachyderm will use a Google Cloud bucket to store the repositories
- Determined will use a Google Cloud bucket to store the models' checkpoints

## Prerequisites ###################################

You will need a Linux machine and some programs in order to operate on the platform. They are:

- **Google Cloud's SDK** : this SDK will be used to create the cluster, the bucket and to perform other operations
- **kubectl** : this command will be used to deploy services on the GKE cluster
- **pachctl** : this command will be used to create the repository and to fill it with data
- **helm**    : this command will be used to deploy the packages containing the services
- **det**     : this command runs the Determined AI shell and allows you to submit experiments
- **docker**  : this command is required to create the container image to serve predictions

### Kubectl

`kubectl` allows you to administer the GKE cluster. Having Google Cloud's SDK installed, it can be easily installed issuing:

```
gcloud components install kubectl
```

Otherwise, it can be installed issuing the following command:

```
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
```

### Pachctl

`pachctl` allows you to administer the Pachyderm's repositories. It can be installed issuing the following command:

```
curl -o /tmp/pachctl.tar.gz -L https://github.com/pachyderm/pachyderm/releases/download/v2.1.3/pachctl_2.1.3_linux_amd64.tar.gz \
      && tar -xvf /tmp/pachctl.tar.gz -C /tmp && sudo cp /tmp/pachctl_2.1.3_linux_amd64/pachctl /usr/local/bin
```

After installation, you can check if the client side is working. You should get version 2.1.3 as in the example below:

```
pachctl version --client-only
2.1.3
```

### Helm

Helm can be installed with just one command:

```
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

If you want more information on Helm installation, you can find it [here](https://helm.sh/docs/intro/install/).


### Det

With Python 3.7 (or above) installed, the `det` command can be installed with just issuing:

```
pip install determined
```

## Setting up the environment ###################################

### Creating the cluster

We will create a cluster called `determined-seldon-cluster`. It will have 2 node pools:

- A node pool with a single non accelerated node, to host the Determined's master, Pachyderm and Seldon
- A GPU accelerated node pool with autoscaling capabilities where each node will have 8 vCPUs, 30GB of memory and 4 NVIDIA K80 GPUs. 

The cluster can be created just running the provided `create-cluster.sh` script: you only need to change the project's name (which is `determined-ai`) at the beginning and maybe some other default. This script will:

- Create the cluster with the default node pool
- Create the second, GPU accelerated, node pool for the cluster
- Enable GPU acceleration on the cluster (it simply runs the following command: `kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml`)
- Create the bucket to store Determined's checkpoints

After we have our cluster up & running, we have to open an extra port in the GCP firewall, in order to allow Seldon to connect to Istio (as it is documented [here](https://istio.io/latest/docs/setup/platform-setup/gke/) ). We first need to figure out the name of the firewall use that has been created for us and this is achieved through the gcloud command. Example:

```
gcloud compute firewall-rules list --filter="name~gke-determined-seldon-cluster-[0-9a-z]*-master"
NAME                                           NETWORK  DIRECTION  PRIORITY  ALLOW              DENY  DISABLED
gke-determined-seldon-cluster-e3e95d04-master  primary  INGRESS    1000      tcp:10250,tcp:443        False
```

After we get the firewall rule, we simply update it this way:

```
gcloud compute firewall-rules update gke-determined-seldon-cluster-e3e95d04-master --allow tcp:10250,tcp:443,tcp:15017
Updated [https://www.googleapis.com/compute/v1/projects/determined-ai/global/firewalls/gke-determined-seldon-cluster-e3e95d04-master].
```

### Creating the buckets

The checkpoint bucket has been created with the script above, so we just need to create the bucket to store Pachyderm's repositories. It can be created with the following command:

``` 
gsutil mb -l us-central1 gs://determined-seldon-data
```

### Installing Pachyderm

The first step is to include Pachyderm's repository to Helm:

```
helm repo add pach https://helm.pachyderm.com
helm repo update
```

Next, a CloudSQL instance for PostgreSQL must be created. If you want to use the provided `pachyderm-values.yaml` you have to create a `pachyderm` database with a `pachyderm` user having `postgres.123` as password. In addition, the Cloud DNS zone named `determined` must be created with the `pachyderm-db` entry pointing to the CloudSQL's IP address. You may look at the provided `pachyderm-values.yaml` for the details.

The next step is to install Pachyderm, using the provided `pachyderm-values.yaml` file:

```
helm install pachyderm -f pachyderm-values.yaml pach/pachyderm --version 2.1.3
```

At this point Pachyderm is installed and we only need to link it to our `pachctl` command. First, we need to get the Pachyderm's public address. It can be done this way:

```
kubectl get services | grep pachd-lb | awk '{print $4}'
34.132.165.206

```

Then, the printed IP address (`34.132.165.206` in this case) must be used in the commands below:

```
echo '{"pachd_address": "grpc://34.132.165.206:30650"}' | pachctl config set context "determined-seldon-context" --overwrite
pachctl config set active-context "determined-seldon-context"
pachctl version
```

More installation details for Pachyderm can be found [here](https://docs.pachyderm.com/latest/deploy-manage/deploy/quickstart).


### Installing Determined

The first step would be to download the latest Helm chart and unzip it to a folder. This has been already done for you and you can find the chart inside the `determined-chart` subfolder (version is 0.18.0 and it has been also customized a bit for this example). Determined can be installed issuing this command:

```
helm install determined determined-chart
```

You may also want to issue the following command to get the master's public IP:

```
kubectl get service determined-master-service-determined
```

Save this IP address to the *DET_MASTER* variable (this variable will be used by the `det` command). For example, if the IP address is *35.223.115.122* you have to issue the following command:

```
export DET_MASTER="35.223.115.122"
```

Just for completeness, the Helm chart can be downloaded from here:

```
https://docs.determined.ai/latest/_downloads/389266101877e29ab82805a88a6fc4a6/determined-latest.tgz
```

More installation details on Determined AI on Kubernetes can be found [here](https://docs.determined.ai/latest/sysadmin-deploy-on-k8s/install-on-kubernetes.html).


### Installing Seldon Core

Seldon Core can be installed using Ambassador or Istio. We are going to use Istio and the commands to install it are the following ones:

```
curl -L https://istio.io/downloadIstio | sh -
cd istio-1.13.2
export PATH=$PWD/bin:$PATH
istioctl install --set profile=demo -y
kubectl label namespace default istio-injection=enabled
```

Here, you will probably get a more recent version than 1.13.2. The last command enables Istio on the `default` namespace. Now, we are going to create the Istio gateway:

```
kubectl apply -f - << END
apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: seldon-gateway
  namespace: istio-system
spec:
  selector:
    istio: ingressgateway # use istio default controller
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
END
```

After the installation ends, we can get the IP and port used by Istio:

```
export INGRESS_HOST=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
export INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].port}')
export INGRESS_URL=$INGRESS_HOST:$INGRESS_PORT
echo $INGRESS_URL
35.188.211.234:80
```

This is the address where Istio is listening for predictions. Now, the next step is to install Seldon Core, first creating its namespace and then installing it using Helm:

```
kubectl create namespace seldon-system

helm install seldon-core seldon-core-operator \
    --repo https://storage.googleapis.com/seldon-charts \
    --set usageMetrics.enabled=true \
    --set istio.enabled=true \
    --namespace seldon-system

```

If Seldon is correctly installed, running the `kubectl get pods` command should provide this output:

```
kubectl get pods -n seldon-system
NAME                                         READY   STATUS    RESTARTS   AGE
seldon-controller-manager-7d4c596775-pqccg   1/1     Running   0          16s
```

More installation details for Seldon Core can be found [here](https://docs.seldon.io/projects/seldon-core/en/latest/install/gcp.html).

The last step is to create a dedicated `seldon` namespace to host our deployments:

```
kubectl create namespace seldon
```


## Creating the Pachyderm repository for the dataset ##############

For this example, the ***Dogs vs Cats*** dataset will be considered. It can be downloaded from Kaggle and it is located at the following address:

https://www.kaggle.com/c/dogs-vs-cats/data?select=train.zip

After you have agreed to the terms & conditions, you can download the train dataset (`train.zip`). This dataset has to be unzipped inside the `pachyderm` folder. You should end up with the following structure:

```
pachyderm
    train
        cat.1.jpg
        dog.1.jpg
        ...
```

This dataset contains 25000 images that will be used for the training. Here is an example of a dog and a cat present inside the dataset:

![Dog](pachyderm/sample/dog.jpg)
![Cat](pachyderm/sample/cat.jpg)

Now, from within the `pachyderm` folder, we will first create the dataset repository:

```
cd pachyderm
pachctl create repo dogs-and-cats
```

Then, we will populate it with the images. Here are the commands to do that:

```
python3 create-dataset.py
pachctl put file dogs-and-cats@master:/data.tar.gz -f data.tar.gz
pachctl list repo
```

From the `pachctl list repo` command you should see an output like this one:

```
NAME          CREATED     SIZE (MASTER) DESCRIPTION 
dogs-and-cats 2 hours ago ≤ 534.6MiB   
```

Now, if you are using Pachyderm Enterprise, you have to generate a token and provide read access to our repository. The token is generate with the following command:

```
pachctl auth get-robot-token seldon
```

You will get an output like the following one:

```
Token: 3cb22a223d0d4b9c90cb88b4fc2a48bb
```

The value of the token must be put inside the const.yaml file. Now, we provide read-only access to our token:

```
pachctl auth set repo dogs-and-cats repoReader robot:seldon
```

## Running the experiment

Now, we are almost ready to run our first experiment. We only need to set the Pachyderm's public IP address inside a couple of configuration files. To do that, just enter the `experiment` folder, edit the `const.yaml` file and change the `host` and `token` properties inside the `pachyderm` entry.

We first authenticate to the Determined's cluster (the password is `xxx`, set inside the deployment descriptor) and then issue the command to create the experiment:

```
det user login determined
det experiment create const.yaml .
```

Now, we can navigate the user interface to see our new experiment being trained. You should see something like this:

![screenshot](experiment-training.png)

Once the training is finished, pick up a checkpoint and register it. You have to select "New model" to create a new model. Choose `dogcat-model` as the model name (we will use it later, in the prediction stage). You should have a model in the repository like the one shown below:

![screenshot](model-repository.png)


## Creating the image for Seldon

Before creating the image, we have to create a service account on the GCP and generate a key for it. The account may have a generic name but it must have the "Storage Object Viewer" role. During the creation, download the JSON key file, which must be put inside the 'seldon' folder with the  'service-account.json' name. This key will allow the prediction code to access the bucket to download the checkpoint. 

Now, we have to create the Docker image that will be run on Seldon. Let's go inside the `seldon` folder and run the image building process with Docker:

```
cd seldon
docker build --tag gcr.io/determined-ai/seldon/image-classification-model:1.0 .
```

After this step, you should see the new image in your local repository:

```
docker image list
REPOSITORY                                               TAG       IMAGE ID       CREATED          SIZE
gcr.io/determined-ai/seldon/image-classification-model   1.0       c38bf57a9549   16 minutes ago   3.71GB
```

Now, we need to push our image to Google Cloud Registry (GCR), where it will be pulled by Seldon on our Kubernetes cluster:

```
docker push gcr.io/determined-ai/seldon/image-classification-model:1.0
```

## Serving the image with Seldon

We can test if the prediction code works locally running the predict_local.py file (we just need to change the DETERMINED_HOST string). 


In order to deploy our container on Seldon Core, we have to edit the 'serve.yaml' file changing the DETERMINED_HOST with the proper value. Then, the deploy is created using the `kubectl` command:

```
kubectl apply -f serve.yaml 
seldondeployment.machinelearning.seldon.io/dogcat-deploy created
```

We can use the `kubectl` command to check when the deploy is ready. We will see an output like the following one:

```
kubectl get pods -n seldon
NAME                                                              READY   STATUS    RESTARTS   AGE
dogcat-deploy-default-0-dogcat-deploy-container-5b8549d7c4mntlx   3/3     Running   1          14m
```

If your deploy won't come up, you can use the usual `kubectl` command to analyze its logs:

```
kubectl logs -f dogcat-deploy-default-0-dogcat-deploy-container-5b8549d7c4mntlx -n seldon -c dogcat-deploy-container
```

## Getting predictions

The last step is to call our deployment to get predictions and we have the `predict_web.py` code  to do that. We have to edit that file to change the DEPLOY_IP with Istio's public IP. Running the code, you should see a window opening like the following one:

![screenshot](prediction.png)
