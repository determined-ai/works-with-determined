import os
import time
import argparse
import yaml

from seldon_deploy_sdk import (
    Configuration, ApiClient, SeldonDeploymentsApi,
    SeldonDeployment, ObjectMeta, SeldonDeploymentSpec, PredictorSpec, SeldonPodSpec, PodSpec, Container,
    PredictiveUnit, Parameter,
    DriftDetectorApi, DetectorConfigData, DetectorConfiguration, BasicDetectorConfiguration,
    DetectorDeploymentConfiguration,
    OutlierDetectorApi, VolumeMount, Volume, SecretVolumeSource, EnvVar
)

from seldon_deploy_sdk.auth import OIDCAuthenticator
from seldon_deploy_sdk.auth.base import AuthMethod
from seldon_deploy_sdk.rest import ApiException

# =====================================================================================

def parse_args():
    parser = argparse.ArgumentParser(description="Deploy a model to Seldon Deploy")
    parser.add_argument("--deploy-name",       type=str, help="Name of the resulting SeldonDeployment")
    parser.add_argument("--detect-bucket-uri", type=str, help="Bucket to use for all detectors")
    parser.add_argument("--detect-batch-size", type=str, help="Batch size to use for all detectors")
    parser.add_argument("--serving-image",     type=str, help="Container image to use to serve the model")
    return parser.parse_args()

# =====================================================================================

def deploy(args, secrets):
    return secrets.namespace + "/" + args.deploy_name

# =====================================================================================

def create_client(secrets) -> ApiClient:
    print("Connecting to Seldon at : " + secrets.seldon_url)
    config = Configuration()
    config.host               = secrets.seldon_url + "/seldon-deploy/api/v1alpha1"
    config.oidc_client_id     = "sd-api"
    config.oidc_server        = secrets.seldon_url + "/auth/realms/deploy-realm"
    config.oidc_client_secret = secrets.client_secret
    config.auth_method        = AuthMethod.CLIENT_CREDENTIALS
    config.verify_ssl         = False

    # Authenticate against an OIDC provider
    auth = OIDCAuthenticator(config)
    config.id_token = auth.authenticate()
    print("Connected.")

    return ApiClient(config)

# =====================================================================================

def build_metadata(model):
    return "---\n" \
           "name: {0}\n" \
           "versions: [ {1} ]\n" \
           "platform: seldon\n" \
            "custom:\n" \
           "    repository: {2}\n" \
           "    pipeline: {3}"\
            .format(model.name, model.version, model.repository, model.pipeline)

# =====================================================================================

def create_deploy_descriptor(args, secrets, det, model):
    return SeldonDeployment(
        api_version="machinelearning.seldon.io/v1",
        kind="SeldonDeployment",
        metadata=ObjectMeta(
            name=args.deploy_name,
            namespace=secrets.namespace
        ),
        spec=SeldonDeploymentSpec(
            name=args.deploy_name,
            predictors=[
                PredictorSpec(
                    component_specs=[
                        SeldonPodSpec(
                            spec=PodSpec(
                                containers=[
                                    Container(
                                        name=args.deploy_name + "-container",
                                        image=args.serving_image,
                                        volume_mounts=[
                                            VolumeMount(
                                                name="config",
                                                mount_path="/app/config"
                                            )
                                        ],
                                        env=[
                                            EnvVar(
                                                name="MODEL_METADATA",
                                                value=build_metadata(model)
                                            )
                                        ]
                                    )
                                ],
                                volumes=[
                                    Volume(
                                        name="config",
                                        secret=SecretVolumeSource(
                                            secret_name="deployment-secret"
                                        )
                                    )
                                ]
                            )
                        )
                    ],
                    name="default",
                    replicas=1,
                    graph=PredictiveUnit(
                        name=args.deploy_name + "-container",
                        type="MODEL",
                        parameters=[
                            Parameter("det_master",    "STRING", det.master),
                            Parameter("user",          "STRING", det.username),
                            Parameter("password",      "STRING", det.password),
                            Parameter("model_name",    "STRING", model.name),
                            Parameter("model_version", "STRING", model.version)
                        ],
                    ),
                    traffic=100,
                )
            ],
        ),
    )

# =====================================================================================

def deploy_model(api_client, args, secrets, det, model):
    api_instance = SeldonDeploymentsApi(api_client)

    descriptor = create_deploy_descriptor(args, secrets, det, model)

    try:
        api_instance.delete_seldon_deployment(args.deploy_name, secrets.namespace)
    except ApiException:
        pass

    try:
        time.sleep(3)
        api_instance.create_seldon_deployment(secrets.namespace, descriptor)
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
                drift_batch_size=args.detect_batch_size,
                storage_uri=args.detect_bucket_uri + "/seldon/drift_detector"
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
                storage_uri=args.detect_bucket_uri + "/seldon/outlier_detector"
            )
        )
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
        self.master   = os.getenv("DET_MASTER")
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

                self.name       = info["name"]
                self.version    = info["version"]
                self.pipeline   = info["pipeline"]
                self.repository = info["repo"]

                print(f"Loaded model info: name='{self.name}', version='{self.version}', pipeline='{self.pipeline}', repo='{self.repository}'")
            except yaml.YAMLError as exc:
                print(exc)

# =====================================================================================

class SecretInfo:
    def __init__(self):
        self.seldon_url    = os.getenv("SEL_URL")
        self.client_secret = os.getenv("SEL_SECRET")
        self.namespace     = os.getenv("SEL_NAMESPACE")

# =====================================================================================

def main():
    args    = parse_args()
    det     = DeterminedInfo()
    model   = ModelInfo("/pfs/data/model-info.yaml")
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
