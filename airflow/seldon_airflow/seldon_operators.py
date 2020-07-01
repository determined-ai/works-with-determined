import argparse
import sys
import time
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from kubernetes import client, config


def seldon_deploy(ds, **kwargs):
    name = kwargs['params']['deploy_name']
    namespace = kwargs['params']['deploy_namespace']
    det_master = kwargs['params']['det_master']
    image = kwargs['params']['deploy_image']

    task_instance = kwargs['task_instance']
    experiment_id = task_instance.xcom_pull(task_ids='train')

    template = """
    apiVersion: machinelearning.seldon.io/v1alpha2
    kind: SeldonDeployment
    metadata:
      name: mnist-prod
    spec:
      name: mnist-prod
      predictors:
      - componentSpecs:
        - spec:
            containers:
            - name: classifier
              image: davidhershey/seldon-mnist:1.3
        graph:
          children: []
          parameters:
            - name: det_master
              type: STRING
              value: "DET_MASTER_ADDR"
            - name: experiment_id
              type: INT
              value: "1"
          endpoint:
            type: REST
          name: classifier
          type: MODEL
        name: mnist-prod
        replicas: 1
    """
    template = yaml.safe_load(template)
    # template = yaml.load(open('serve.yaml', 'r'), Loader=Loader)

    config.load_kube_config()
    api = client.CustomObjectsApi()

    template["metadata"]["name"] = name
    template["spec"]["name"] = name
    template["spec"]["predictors"][0]["name"] = name

    template["metadata"]["namespace"] = namespace

    template["spec"]["predictors"][0]["graph"]["parameters"] = [
        {'name': 'det_master', 'type': 'STRING', 'value': det_master},
        {'name': 'experiment_id', 'type': 'INT', 'value': str(experiment_id)},
    ]

    template["spec"]["predictors"][0]["componentSpecs"][0]['spec']['containers'][0]['image'] = image

    try:
        resource = api.get_namespaced_custom_object(
            group="machinelearning.seldon.io",
            version="v1alpha2",
            name=name,
            namespace=namespace,
            plural="seldondeployments",
        )
        api.delete_namespaced_custom_object(
            group="machinelearning.seldon.io",
            version="v1alpha2",
            name=name,
            namespace=namespace,
            plural="seldondeployments",
            body=client.V1DeleteOptions(),
        )
        print("Resource deleted")
    except:
        pass
    api.create_namespaced_custom_object(
        group="machinelearning.seldon.io",
        version="v1alpha2",
        namespace=namespace,
        plural="seldondeployments",
        body=template,
    )
    print("Resource created")

    def is_ready():
        status = api.get_namespaced_custom_object_status(
            group="machinelearning.seldon.io",
            version="v1alpha2",
            name=name,
            namespace=namespace,
            plural="seldondeployments",
        )
        if 'status' not in status:
            print('No Status')
            return False
        status = status['status']['state']
        if status == 'Available':
            return True
        if status == 'Creating':
            return False
        if status == "Failed":
            sys.exit(-1)

    start_time = time.time()
    while not is_ready():
        time.sleep(2)
        if time.time() - start_time > 300: # 5 minute timeout
            print("Timeout waiting for service to start")
            sys.exit(-1)

    v1 = client.CoreV1Api()
    svc = v1.read_namespaced_service('istio-ingressgateway', 'istio-system')
    gateway = svc.to_dict()['status']['load_balancer']['ingress'][0]['hostname']
    endpoint = "http://" + gateway + f'/seldon/{namespace}/{name}/api/v1.0/predictions'
    return endpoint
