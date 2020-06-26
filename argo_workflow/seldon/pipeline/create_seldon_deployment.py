åimport argparse
import sys
import time
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from kubernetes import client, config

def main():
    parser = argparse.ArgumentParser(description='Run Determined Example')
    parser.add_argument('name', type=str, help='deployment name')
    parser.add_argument('namespace', type=str, help='deployment namespace')
    parser.add_argument('det_master', type=str, help='determined master address')
    parser.add_argument('experiment_id', type=str, help='experiment to deploy')
    parser.add_argument('--image', type=str, help='model image', default='davidhershey/seldon-mnist:1.3')
    parser.add_argument('--local', action='store_true')
    args = parser.parse_args()

    template = yaml.load(open('serve.yaml', 'r'), Loader=Loader)

    if args.local:
        config.load_kube_config()
    else:
        config.load_incluster_config()

    api = client.CustomObjectsApi()

    template["metadata"]["name"] = args.name
    template["spec"]["name"] = args.name
    template["spec"]["predictors"][0]["name"] = args.name

    template["metadata"]["namespace"] = args.namespace

    template["spec"]["predictors"][0]["graph"]["parameters"] = [
        {'name': 'det_master', 'type': 'STRING', 'value': args.det_master},
        {'name': 'experiment_id', 'type': 'INT', 'value': args.experiment_id},
    ]

    template["spec"]["predictors"][0]["componentSpecs"][0]['spec']['containers'][0]['image'] = args.image

    try:
        resource = api.get_namespaced_custom_object(
            group="machinelearning.seldon.io",
            version="v1alpha2",
            name=args.name,
            namespace=args.namespace,
            plural="seldondeployments",
        )
        api.delete_namespaced_custom_object(
            group="machinelearning.seldon.io",
            version="v1alpha2",
            name=args.name,
            namespace=args.namespace,
            plural="seldondeployments",
            body=client.V1DeleteOptions(),
        )
        print("Resource deleted")
    except:
        pass
    api.create_namespaced_custom_object(
        group="machinelearning.seldon.io",
        version="v1alpha2",
        namespace=args.namespace,
        plural="seldondeployments",
        body=template,
    )
    print("Resource created")

    def is_ready():
        status = api.get_namespaced_custom_object_status(
            group="machinelearning.seldon.io",
            version="v1alpha2",
            name=args.name,
            namespace=args.namespace,
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
    endpoint =  "http://" + gateway + f'/seldon/{args.namespace}/{args.name}/api/v1.0/predictions'
    with open('/tmp/endpoint.txt', 'w') as f:
        f.write(endpoint)


if __name__ == "__main__":
    main()
