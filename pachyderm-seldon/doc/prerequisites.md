 
# Software prerequisites ###################################

You will need a Linux machine and some programs in order to operate on the platform. They are:

- **Google Cloud's SDK** : this SDK will be used to create the cluster, the bucket and to perform other operations
- **kubectl** : this command will be used to deploy services on the GKE cluster
- **pachctl** : this command will be used to create the repository and to fill it with data
- **helm**    : this command will be used to deploy the packages containing the components (Pachyderm, Determined and Seldon)
- **docker**  : this command is required to create the container image to serve predictions

## Kubectl

`kubectl` allows you to administer the GKE cluster. Having Google Cloud's SDK installed, it can be easily installed issuing:

```
gcloud components install kubectl
```

Otherwise, it can be installed issuing the following command:

```
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
```

Once the binary has been downloaded, just remember to copy it into your path (like `~/bin`, `/usr/local/bin` or any other folder included into your path).


## Pachctl

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

## Helm

Helm can be installed with just one command:

```
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

Once downloaded, the Helm binary needs to be copied into your path as previously described. If you want more information on Helm installation, you can find it [here](https://helm.sh/docs/intro/install/).


## Det

With Python 3.7 (or above) installed, the `det` command can be installed with just issuing:

```
pip install determined
```

---
[Up](../README.md) | [Next](environment.md)