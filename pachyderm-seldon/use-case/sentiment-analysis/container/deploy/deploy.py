import argparse
import os
import time

import xxlimited
import yaml
from seldon_deploy_sdk import (
    ApiClient,
    BasicDetectorConfiguration,
    Configuration,
    Container,
    DetectorConfigData,
    DetectorConfiguration,
    DetectorDeploymentConfiguration,
    DriftDetectorApi,
    EnvVar,
    HostPathVolumeSource,
    ObjectMeta,
    OutlierDetectorApi,
    Parameter,
    PodSpec,
    PredictiveUnit,
    PredictorSpec,
    ResourceList,
    ResourceRequirements,
    SecretVolumeSource,
    SeldonDeployment,
    SeldonDeploymentsApi,
    SeldonDeploymentSpec,
    SeldonPodSpec,
    Volume,
    VolumeMount,
)
from seldon_deploy_sdk.auth import OIDCAuthenticator
from seldon_deploy_sdk.auth.base import AuthMethod
from seldon_deploy_sdk.rest import ApiException

# =====================================================================================


def parse_args():
    parser = argparse.ArgumentParser(description="Deploy a model to Seldon Deploy")
    parser.add_argument("--deploy-name", type=str, help="Name of the resulting SeldonDeployment")
    parser.add_argument("--detect-bucket-uri", type=str, help="Bucket to use for all detectors")
    parser.add_argument("--detect-batch-size", type=str, help="Batch size to use for all detectors")
    parser.add_argument("--serving-image", type=str, help="Container image to use to serve the model")
    return parser.parse_args()


# =====================================================================================


def deploy(args, secrets):
    return secrets.namespace + "/" + args.deploy_name


# =====================================================================================


def create_client(secrets) -> ApiClient:
    print("Connecting to Seldon at : " + secrets.seldon_url)
    config = Configuration()
    config.host = secrets.seldon_url + "/seldon-deploy/api/v1alpha1"
    config.oidc_client_id = "sd-api"
    config.oidc_server = secrets.seldon_url + "/auth/realms/deploy-realm"
    config.oidc_client_secret = secrets.client_secret
    config.auth_method = AuthMethod.CLIENT_CREDENTIALS
    config.verify_ssl = False
    # Authenticate against an OIDC provider
    # auth = OIDCAuthenticator(config)
    # config.id_token = auth.authenticate()
    # print("Connected.")

    auth = OIDCAuthenticator(config)
    config.id_token = auth.authenticate()
    api_client = ApiClient(configuration=config, authenticator=auth)
    return api_client


# =====================================================================================


def build_metadata(model):
    return (
        "---\n"
        "name: {0}\n"
        "versions: [ {1} ]\n"
        "platform: seldon\n"
        "custom:\n"
        "    repository: {2}\n"
        "    pipeline: {3}".format(model.name, model.version, model.repository, model.pipeline)
    )


# =====================================================================================


def deploy_model(api_client, args, secrets, det, model):
    api_instance = SeldonDeploymentsApi(api_client)

    CPU_REQUESTS = "16"
    MEMORY_REQUESTS = "32Gi"

    CPU_LIMITS = "16"
    MEMORY_LIMITS = "32Gi"

    mldeployment = {
        "kind": "SeldonDeployment",
        "metadata": {"name": args.deploy_name, "namespace": secrets.namespace, "labels": {"fluentd": "true"}},
        "apiVersion": "machinelearning.seldon.io/v1alpha2",
        "spec": {
            "name": args.deploy_name,
            "annotations": {"seldon.io/engine-seldon-log-messages-externally": "true"},
            "protocol": "seldon",
            "predictors": [
                {
                    "componentSpecs": [
                        {
                            "spec": {
                                "containers": [
                                    {
                                        "name": f"{args.deploy_name}-container",
                                        "image": args.serving_image,
                                        "env": [
                                            {
                                                "name": "MODEL_METADATA",
                                                "value": build_metadata(model),
                                            },
                                            {
                                                "name": "GUNICORN_THREADS",
                                                "value": "16",
                                            },
                                        ],
                                        "volumeMounts": [
                                            {
                                                "name": "det-checkpoints",
                                                "mountPath": "/determined_shared_fs",
                                            },
                                        ],
                                        "resources": {
                                            "requests": {"cpu": CPU_REQUESTS, "memory": MEMORY_REQUESTS},
                                            "limits": {"cpu": CPU_LIMITS, "memory": MEMORY_LIMITS},
                                        },
                                    },
                                ],
                                "volumes": [
                                    {
                                        "name": "det-checkpoints",
                                        "hostPath": {"path": "/mnt/mapr_nfs/determined/det_checkpoints", "type": ""},
                                    },
                                ],
                            }
                        }
                    ],
                    "name": "default",
                    "replicas": 1,
                    "traffic": 100,
                    "graph": {
                        "name": f"{args.deploy_name}-container",
                        "parameters": [
                            {
                                "name": "det_master",
                                "value": det.master,
                                "type": "STRING",
                            },
                            {
                                "name": "user",
                                "value": det.username,
                                "type": "STRING",
                            },
                            {
                                "name": "password",
                                "value": det.password,
                                "type": "STRING",
                            },
                            {
                                "name": "model_name",
                                "value": model.name,
                                "type": "STRING",
                            },
                            {
                                "name": "model_version",
                                "value": model.version,
                                "type": "STRING",
                            },
                        ],
                        "children": [],
                        "logger": {"mode": "all"},
                    },
                }
            ],
        },
        "status": {},
    }

    try:
        api_instance.delete_seldon_deployment(args.deploy_name, secrets.namespace)
    except ApiException:
        pass

    try:
        time.sleep(3)
        api_instance.create_seldon_deployment(secrets.namespace, mldeployment=mldeployment)
        print(f"Deployment '{deploy(args, secrets)}' created")
        return True
    except ApiException as e:
        print(f"Deployment of '{deploy(args, secrets)}' failed: %s\n" % e)
        return False


# =====================================================================================


def create_drift_detector(api_client, args, secrets, model):
    api_instance = DriftDetectorApi(api_client)
    drift_detector = DetectorConfigData(
        name=args.deploy_name,
        config=DetectorConfiguration(
            deployment=DetectorDeploymentConfiguration(
                model_name=model.version[:5],
                event_type="io.seldon.serving.inference.drift",
                event_source="io.seldon.serving.seldon-seldondeployment-{}-drift".format(args.deploy_name),
                reply_url="http://seldon-request-logger.seldon-logs",
                protocol="seldon.http",
                http_port="8080",
                user_permission=8888,
            ),
            basic=BasicDetectorConfiguration(
                drift_batch_size=args.detect_batch_size, storage_uri=args.detect_bucket_uri + "/seldon/drift_detector"
            ),
        ),
    )

    try:
        api_instance.delete_drift_detector_seldon_deployment(args.deploy_name, secrets.namespace, args.deploy_name)
    except ApiException:
        pass

    try:
        time.sleep(3)
        api_instance.create_drift_detector_seldon_deployment(args.deploy_name, secrets.namespace, drift_detector)
        print(f"Drift detector '{deploy(args, secrets)}' created")
        return True
    except ApiException as e:
        print(f"Deployment of drift detector '{deploy(args, secrets)}' failed: %s\n" % e)
        return False


# =====================================================================================


def create_outlier_detector(api_client, args, secrets, model):
    api_instance = OutlierDetectorApi(api_client)
    outlier_detector = DetectorConfigData(
        name=args.deploy_name,
        config=DetectorConfiguration(
            deployment=DetectorDeploymentConfiguration(
                model_name=model.version[:5],
                event_type="io.seldon.serving.inference.outlier",
                event_source="io.seldon.serving.seldon-seldondeployment-{}-outlier".format(args.deploy_name),
                reply_url="http://seldon-request-logger.seldon-logs",
                protocol="seldon.http",
                http_port="8080",
                user_permission=8888,
            ),
            basic=BasicDetectorConfiguration(
                drift_batch_size=args.detect_batch_size,
                storage_uri=args.detect_bucket_uri + "/seldon/outlier_detector",
            ),
        ),
    )

    try:
        api_instance.delete_outlier_detector_seldon_deployment(args.deploy_name, secrets.namespace, args.deploy_name)
    except ApiException:
        pass

    try:
        time.sleep(3)
        api_instance.create_outlier_detector_seldon_deployment(args.deploy_name, secrets.namespace, outlier_detector)
        print(f"Outlier detector '{deploy(args, secrets)}' created")
        return True
    except ApiException as e:
        print(f"Deployment of outlier detector '{deploy(args, secrets)}' failed: %s\n" % e)
        return False


# =====================================================================================


def wait_for_deployment(api_client, args, secrets):
    api_instance = SeldonDeploymentsApi(api_client)

    try:
        while True:
            api_response = api_instance.read_seldon_deployment(args.deploy_name, secrets.namespace)
            if api_response.status.state == "Available":
                print(f"Deployment of '{deploy(args, secrets)} is ready")
                break
            else:
                print(f"Waiting for deployment of '{deploy(args, secrets)}...")
                time.sleep(5)
        time.sleep(5)
    except ApiException as e:
        print(f"Raised error while waiting for deployment of '{deploy(args, secrets)}: %s\n" % e)
        pass


# =====================================================================================


class DeterminedInfo:
    def __init__(self):
        self.master = os.getenv("DET_MASTER")
        self.username = os.getenv("DET_USER")
        self.password = os.getenv("DET_PASSWORD")


# =====================================================================================


class ModelInfo:
    def __init__(self, file):
        print(f"Reading model info file: {file}")
        info = {}
        with open(file, "r") as stream:
            try:
                info = yaml.safe_load(stream)

                self.name = info["name"]
                self.version = info["version"]
                self.pipeline = info["pipeline"]
                self.repository = info["repo"]

                print(
                    f"Loaded model info: name='{self.name}', version='{self.version}', pipeline='{self.pipeline}', repo='{self.repository}'"
                )
            except yaml.YAMLError as exc:
                print(exc)


# =====================================================================================


class SecretInfo:
    def __init__(self):
        self.seldon_url = os.getenv("SEL_URL")
        self.client_secret = os.getenv("SEL_SECRET")
        self.namespace = os.getenv("SEL_NAMESPACE")


# =====================================================================================


def main():
    args = parse_args()
    det = DeterminedInfo()

    model = ModelInfo("/pfs/data/model-info.yaml")
    secrets = SecretInfo()

    print(f"Starting pipeline: deploy-name='{args.deploy_name}', model='{model.name}', version='{model.version}'")

    api_client = create_client(secrets)

    if not deploy_model(api_client, args, secrets, det, model):
        return

    if not create_drift_detector(api_client, args, secrets, model):
        return

    if not create_outlier_detector(api_client, args, secrets, model):
        return

    wait_for_deployment(api_client, args, secrets)

    print(f"Ending pipeline: deploy-name='{args.deploy_name}', model='{model.name}', version='{model.version}'")


# =====================================================================================


if __name__ == "__main__":
    main()
