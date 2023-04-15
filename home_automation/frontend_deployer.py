#!/usr/bin/python3
# pylint: disable=invalid-name
"""Deploy frontend container in k8s."""
import argparse
import base64
import json
import logging
import re
from typing import List, Tuple

import docker
import docker.errors
import semver
from docker.models.images import Image
from kubernetes import client as klient

import home_automation
from home_automation import utilities
from home_automation.config import Config, ConfigError, load_config
from home_automation.server.backend.state_manager import StateManager

logging.basicConfig(level=logging.INFO)


def _get_image_tag(config: Config) -> str:
    """Return the image tag."""
    pattern = r"^(?P<image>([a-z\d_\-\.]*(:\d+)?/)?[a-z\d]+[a-z\d_\-\.]*)(?P<tag>:[\w\.\-]+)?$"
    match = re.match(pattern, config.frontend.image_name)
    if match:
        if match.group("tag"):
            raise ConfigError(
                f"Invalid frontend image name '{config.frontend.image_name}'. \
Image name already contains a tag."
            )
    else:
        raise ValueError(f"Invalid frontend image name '{config.frontend.image_name}'.")
    return f"{config.frontend.image_name}:{home_automation.VERSION}"


def _create_new_namespace_if_necessary(config: Config):
    """Create the namespace if it doesn't exist."""
    k_client = utilities.get_k8s_client(config)
    v1 = klient.CoreV1Api(k_client)
    namespaces = v1.list_namespace().items
    namespaces = list(
        filter(lambda n: n.metadata.name == config.frontend.namespace, namespaces)
    )
    if len(namespaces) == 0:
        logging.info("Namespace '%s' not found, creating...", config.frontend.namespace)
        v1.create_namespace(
            klient.V1Namespace(
                metadata=klient.V1ObjectMeta(name=config.frontend.namespace)
            )
        )
        logging.info("Created namespace.")
    else:
        logging.info("Namespace found.")


def _get_new_deployment(config: Config) -> klient.V1Deployment:
    tag = _get_image_tag(config)
    _, registry_name = _parse_registry_url(config)
    env_vars = [
        klient.V1EnvVar(
            name="BACKEND_IP_ADDRESS",
            value=config.frontend.backend_ip_address,
        ),
        klient.V1EnvVar(
            name="HOME_AUTOMATION_VERSION",
            value=home_automation.VERSION,
        ),
    ]
    if config.heimdall.url:
        env_vars.append(klient.V1EnvVar(name="HEIMDALL_URL", value=config.heimdall.url))
    return klient.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=klient.V1ObjectMeta(
            name=config.frontend.deployment_name, namespace=config.frontend.namespace
        ),
        spec=klient.V1DeploymentSpec(
            replicas=config.frontend.replicas,
            selector=klient.V1LabelSelector(
                match_labels={"app": "home-automation", "role": "frontend"}
            ),
            template=klient.V1PodTemplateSpec(
                metadata=klient.V1ObjectMeta(
                    labels={"app": "home-automation", "role": "frontend"}
                ),
                spec=klient.V1PodSpec(
                    containers=[
                        klient.V1Container(
                            name="frontend",
                            image=tag,
                            ports=[klient.V1ContainerPort(container_port=80)],
                            env=env_vars,
                            liveness_probe=klient.V1Probe(
                                http_get=klient.V1HTTPGetAction(
                                    path="/status", port=80
                                ),
                            ),
                        )
                    ],
                    image_pull_secrets=[
                        klient.V1LocalObjectReference(name=registry_name)
                    ],
                ),
            ),
        ),
    )


def _get_new_service(config: Config) -> klient.V1Service:
    return klient.V1Service(
        api_version="v1",
        kind="Service",
        metadata=klient.V1ObjectMeta(
            name=config.frontend.service_name, namespace=config.frontend.namespace
        ),
        spec=klient.V1ServiceSpec(
            selector={"app": "home-automation", "role": "frontend"},
            ports=[klient.V1ServicePort(port=80, target_port=80)],
        ),
    )


def _parse_registry_url(config: Config) -> Tuple[str, str]:
    assert config.docker.registry
    pattern = r"^https?://(?P<host>[\w\-\.]+)(?P<port>:\d+)?$"
    match = re.match(pattern, config.docker.registry.registry_url)
    if not match:
        raise ValueError(
            f"Invalid registry URL '{config.docker.registry.registry_url}'. \
Could not extract host from it."
        )
    host = match.group("host")
    registry_name = host.replace(".", "-")
    return host, registry_name


def _get_new_registry_authentication_secret(config: Config) -> klient.V1Secret:
    assert config.docker.registry
    assert config.docker.registry.auth
    host, registry_name = _parse_registry_url(config)
    data = {
        "auths": {
            host: {
                "username": config.docker.registry.auth.username,
                "password": config.docker.registry.auth.password,
            }
        }
    }
    encoded = base64.b64encode(json.dumps(data).encode("utf-8"))
    return klient.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=klient.V1ObjectMeta(
            name=registry_name,
            namespace=config.frontend.namespace,
        ),
        data={".dockerconfigjson": encoded.decode("utf-8")},
        type="kubernetes.io/dockerconfigjson",
    )


def _create_registry_secret_if_necessary(config: Config):
    """Create the registry secret if it doesn't exist and if credentials are given."""
    if not config.docker.registry or not config.docker.registry.auth:
        return
    _, registry_name = _parse_registry_url(config)
    k_client = utilities.get_k8s_client(config)
    v1 = klient.CoreV1Api(k_client)
    secrets = v1.list_namespaced_secret(namespace=config.frontend.namespace).items
    secrets = list(filter(lambda s: s.metadata.name == registry_name, secrets))
    if len(secrets) == 0:
        logging.info("Registry secret not found, creating...")
        secret = _get_new_registry_authentication_secret(config)
        v1.create_namespaced_secret(namespace=config.frontend.namespace, body=secret)
        logging.info("Created registry secret.")
    else:
        logging.info("Registry secret found.")


def deploy_frontend_service(config: Config):
    """Deploy the frontend service."""
    k_client = utilities.get_k8s_client(config)
    v1 = klient.CoreV1Api(k_client)
    services = v1.list_namespaced_service(namespace=config.frontend.namespace).items
    services = list(
        filter(lambda s: s.metadata.name == config.frontend.service_name, services)
    )
    if len(services) == 0:
        logging.info(
            "Service '%s' not found, creating...", config.frontend.service_name
        )
        service = _get_new_service(config)
        _create_new_namespace_if_necessary(config)
        v1.create_namespaced_service(namespace=config.frontend.namespace, body=service)
        logging.info("Created service.")
    else:
        logging.info("Service found.")


def deploy_frontend_deployment(config: Config):
    """Only deploy the frontend, don't build the image."""
    k_client = utilities.get_k8s_client(config)
    apps_v1 = klient.AppsV1Api(k_client)
    query_result = apps_v1.list_namespaced_deployment(
        namespace=config.frontend.namespace
    ).items
    deploys = list(
        filter(
            lambda d: d.metadata.name == config.frontend.deployment_name, query_result
        )
    )
    new_tag = _get_image_tag(config)
    if len(deploys) == 0:
        logging.info("Deployment not found, creating...")
        deploy = _get_new_deployment(config)
        apps_v1.create_namespaced_deployment(
            namespace=config.frontend.namespace, body=deploy
        )
        logging.info("Created deployment.")
    else:
        dep = deploys[0]
        if dep.spec.template.spec.containers[0].image == new_tag:
            logging.info("Deployment already up to date.")
            return
        dep.spec.template.spec.containers[0].image = new_tag
        logging.info("Updating deployment to image '%s'...", new_tag)
        apps_v1.patch_namespaced_deployment(
            config.frontend.deployment_name,
            namespace=config.frontend.namespace,
            body=dep,
        )
        logging.info("Updated deployment.")


def build_image_if_appropriate(config: Config):
    """Build the image if it is appropriate."""
    client = docker.from_env()
    current_tag = _get_image_tag(config)
    try:
        image: Image = client.images.get(current_tag)
        if current_tag not in image.tags:
            raise docker.errors.ImageNotFound(f"Image '{current_tag}' not found.")
        logging.info("Image '%s' already found.", current_tag)
        state_manager = StateManager(config)
        state_manager.update_status("building_frontend_image", False)
        state_manager.update_status("pushing_frontend_image", False)
    except docker.errors.ImageNotFound:
        logging.info("Image '%s' not found, building...", current_tag)
        build_image(config)


def build_image(config: Config):
    """Build the frontend image."""
    state_manager = StateManager(config)
    state_manager.update_status("building_frontend_image", 1)
    tag = _get_image_tag(config)
    logging.info("Building frontend image under '%s'...", tag)
    client = docker.from_env()
    if config.docker.registry and config.docker.registry.auth:
        client.login(
            username=config.docker.registry.auth.username,
            password=config.docker.registry.auth.password,
            registry=config.docker.registry.registry_url,
        )
    build_args = {"home_automation_version": home_automation.VERSION}
    if config.heimdall.url:
        build_args["heimdall_url"] = config.heimdall.url
    image, log_stream = client.images.build(
        path="home_automation/server/frontend",
        tag=tag,
        nocache=config.docker.build.no_cache,
        network_mode=config.docker.build.network,
        buildargs=build_args,
    )
    for entry in log_stream:
        logging.info(entry.get("stream", entry))
    version = semver.VersionInfo.parse(home_automation.VERSION)
    prod_tag_endings = [
        "latest",
        f"{version.major}",
        f"{version.major}.{version.minor}",
        f"{version.major}.{version.minor}.{version.patch}",
    ]
    prod_tags = [config.frontend.image_name + ":" + tag for tag in prod_tag_endings]
    if not version.prerelease:
        for tag in prod_tags:
            image.tag(tag)
    logging.info("Built image.")
    state_manager.update_status("building_frontend_image", 0)
    logging.info("Pushing image '%s' to registry...", tag)
    state_manager.update_status("pushing_frontend_image", 1)
    results_str = client.images.push(tag)
    if not version.prerelease:
        for tag in prod_tags:
            results_str += "\n" + client.images.push(tag)
    results: List[str] = results_str.replace("\r", "").split("\n")
    potential_errors = list(
        filter(
            lambda r: bool(json.loads(r).get("errorDetail", {}).get("message")),
            filter(None, results),
        )
    )
    if potential_errors:
        logging.error(potential_errors)
        error = json.loads(potential_errors[0])["errorDetail"]["message"]
        logging.error("Error pushing image: %s", error)
        raise DeploymentError(error)
    logging.info("Pushed image.")
    state_manager.update_status("pushing_frontend_image", 0)


def deployonly_frontend(config: Config):
    """Only deploy the frontend deployment/service, don't build the image."""
    _create_new_namespace_if_necessary(config)
    _create_registry_secret_if_necessary(config)
    deploy_frontend_deployment(config)
    deploy_frontend_service(config)


def build_and_deploy_frontend(config: Config):
    """Build & deploy the frontend image/deployment/service."""
    build_image_if_appropriate(config)
    deployonly_frontend(config)


def delete_frontend(config: Config):
    """Delete the frontend, including the namespace."""
    logging.info("Deleting entire frontend (including deployment & namespace)...")
    k_client = utilities.get_k8s_client(config)
    v1 = klient.CoreV1Api(k_client)
    v1.delete_namespace(config.frontend.namespace)
    logging.info("Deleted frontend infrastructure.")


class DeploymentError(Exception):
    "Error for when a step in the deployment process fails."


def main():
    """Deploy the frontend."""
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["deploy", "deployonly", "build", "delete"])
    parser.add_argument("--force", action="store_true")
    parser = utilities.argparse_add_argument_for_config_file_path(parser)
    args = parser.parse_args()
    config = load_config(args.config)
    action = args.action
    if action == "deploy":
        build_and_deploy_frontend(config)
    elif action == "deployonly":
        deployonly_frontend(config)
    elif action == "build":
        if args.force:
            build_image(config)
        else:
            build_image_if_appropriate(config)
    elif action == "delete":
        delete_frontend(config)


if __name__ == "__main__":
    main()
