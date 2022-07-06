#!/bin/bash

PROJECT="determined-ai"
NAME="determined-seldon"
GPU_TYPE="nvidia-tesla-k80"
GPUS_PER_NODE="4"
MAX_NODES="4"

# Other constants

CLUSTER="cluster"
ZONE="us-central1-c"
BUCKET="checkpoint"
CLUSTER_NAME="${NAME}-${CLUSTER}"
BUCKET_NAME="${NAME}-${BUCKET}"

# Create the GKE cluster that will contain only a single non-GPU node.

echo "Creating cluster : ${CLUSTER_NAME}"

gcloud container clusters create ${CLUSTER_NAME} \
	--project ${PROJECT} \
	--zone ${ZONE} \
	--node-locations ${ZONE} \
	--num-nodes "1" \
	--no-enable-basic-auth \
	--cluster-version "1.21.6-gke.1503" \
	--release-channel "regular" \
	--machine-type "n1-standard-16" \
	--image-type "COS_CONTAINERD" \
	--disk-type "pd-standard" \
	--disk-size "100" \
	--metadata disable-legacy-endpoints=true \
	--scopes "https://www.googleapis.com/auth/devstorage.full_control",\
"https://www.googleapis.com/auth/logging.write",\
"https://www.googleapis.com/auth/monitoring",\
"https://www.googleapis.com/auth/servicecontrol",\
"https://www.googleapis.com/auth/service.management.readonly",\
"https://www.googleapis.com/auth/trace.append" \
	--max-pods-per-node "110" \
	--logging=SYSTEM,WORKLOAD \
	--monitoring=SYSTEM \
	--enable-ip-alias \
	--network "projects/${PROJECT}/global/networks/primary" \
	--subnetwork "projects/${PROJECT}/regions/us-central1/subnetworks/primary" \
	--enable-intra-node-visibility \
	--default-max-pods-per-node "110" \
	--enable-dataplane-v2 \
	--enable-master-authorized-networks \
	--addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver \
	--enable-autoupgrade \
	--enable-autorepair \
	--max-surge-upgrade 1 \
	--max-unavailable-upgrade 0 \
	--maintenance-window-start "2022-02-12T23:00:00Z" \
	--maintenance-window-end "2022-02-13T07:00:00Z" \
	--maintenance-window-recurrence "FREQ=WEEKLY;BYDAY=SA,SU" \
	--enable-shielded-nodes \
	--enable-private-nodes \
	--enable-private-endpoint \
	--master-ipv4-cidr "10.100.1.0/28" \
	--enable-master-global-access \
	--tags ${NAME}

# Create a node pool. This will not launch any nodes immediately but will
# scale up and down as needed. If you change the GPU type or the number of
# GPUs per node, you may need to change the machine-type.

echo "Creating nodepool"

gcloud container node-pools create ${NAME}-gpu-node-pool \
  --cluster ${CLUSTER_NAME} \
  --accelerator "type=${GPU_TYPE},count=${GPUS_PER_NODE}" \
  --zone ${ZONE} \
  --num-nodes=0 \
  --enable-autoscaling \
  --min-nodes=0 \
  --max-nodes=${MAX_NODES} \
  --machine-type=n1-standard-4 \
  --scopes=storage-full,cloud-platform

# Deploy a DaemonSet that enables the GPUs.
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml

# Create a GCS bucket to store checkpoints.
gsutil mb gs://${BUCKET_NAME}
