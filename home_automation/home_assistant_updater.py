import httpx
import re
import logging
from kubernetes import client as klient
from kubernetes import config as konfig
from typing import Dict, Tuple, Any, Union
from home_automation.config import Config, ConfigError

PORTAINER_CALLS_TIMEOUT = 5
CURRENT_HASS_VERSION_REGEX = \
    r"image: homeassistant/home-assistant:(?P<version>\d\d\d\d\.\d\d?\.\d+)"


class UpdaterError(Exception):
    """Any error specific to home_assistant_updater"""


async def _log_in_to_portainer(config: Config, client: httpx.AsyncClient) -> Dict[str, str]:
    """Log in to portainer and return authorization header. Might raise ServerAPIError."""
    if not config.portainer:
        raise ConfigError("No portainer configuration provided.")
    if not config.portainer.url:
        raise ConfigError("No portainer URL configured.")
    payload = {"username": config.portainer.username,
               "password": config.portainer.password}
    response = await client.post(
        config.portainer.url + "/api/auth",
        json=payload,
        timeout=PORTAINER_CALLS_TIMEOUT)
    auth_data = response.json()
    jwt = auth_data.get("jwt", None)
    if not jwt:
        raise PermissionError("Forbidden (portainer credentials).")
    return {"authorization": f"Bearer {jwt}"}


async def _get_portainer_stack(
    config: Config,
    client: httpx.AsyncClient,
    headers: Dict[str, str]
) -> Dict[str, str]:
    """Get portainer stack data. Might raise ServerAPIError."""
    if not config.portainer:
        raise ConfigError("No portainer configuration provided.")
    if not config.portainer.url:
        raise ConfigError("No portainer URL configured.")
    if not config.portainer.home_assistant_stack:
        raise ConfigError(
            "No portainer stack defining home assistant configured.")
    response = await client.get(config.portainer.url + "/api/stacks",
                                headers=headers,
                                timeout=PORTAINER_CALLS_TIMEOUT)
    stacks = response.json()
    try:
        pot_stacks = filter(lambda s: s.get("Name", "").lower(
        ) == config.portainer.home_assistant_stack.lower(), stacks)  # type: ignore
        # as it's actually checked for just a few lines above
        stack = list(pot_stacks)[0]
        stack_id = stack.get("Id", None)
        if not stack_id:
            raise UpdaterError("Invalid data received from portainer.")
        response = await client.get(
            config.portainer.url + f"/api/stacks/{stack_id}/file",
            headers=headers,
            timeout=PORTAINER_CALLS_TIMEOUT)
        stack_data = response.json()
        file_content = stack_data.get("StackFileContent", None)
        if not file_content:
            raise UpdaterError(
                "No StackFileContent provided from portainer.")
        stack["stackFileContent"] = file_content
        return stack
    except IndexError as err:
        raise UpdaterError(
            f"Stack '{config.portainer.home_assistant_stack}' not found.") from err


def _get_current_version_from_portainer_stack(stack: Dict[str, str]):
    """Get current home assistant version from stack definition."""
    result = re.search(CURRENT_HASS_VERSION_REGEX, stack["stackFileContent"])
    if not result:
        raise UpdaterError(
            "Could not extract version information from stack info.")
    current_version = result.groupdict().get("version", None)
    return current_version


async def _get_version_to_update_to(
    config: Config,
    client: httpx.AsyncClient,
    user_payload: Dict[str, str] = None
) -> str:
    """Get version of home assistant to update to. Might throw ServerAPIError."""
    if not config.home_assistant:
        raise ConfigError("No Home Assistant configuration provided.")
    if not config.home_assistant.url:
        raise ConfigError("No home assistant URL configured.")
    version_to_update_to = None
    if user_payload:
        if isinstance(user_payload, dict):
            version_to_update_to = user_payload.get(
                "update_to_version", None)
    if not version_to_update_to:
        hass_headers = {
            "authorization": f"Bearer {config.home_assistant.token}"}
        response = await client.get(
            config.home_assistant.url + "/api/states/sensor.docker_hub",
            headers=hass_headers,
            timeout=PORTAINER_CALLS_TIMEOUT)
        data = response.json()
        version_to_update_to = data.get(
            "state", None)
    if not version_to_update_to:
        raise UpdaterError(
            "Could not retreive newest available version from home assistant.")
    return version_to_update_to


async def _update_home_assistant_with_portainer(
    config: Config,
    client: httpx.AsyncClient,
    current_version: str,
    version_to_update_to: str,
    stack: Dict[str, str],
    portainer_headers: Dict[str, str]
) -> Union[Tuple[Dict[str, Any], int], Dict[str, Any]]:
    if not config.portainer:
        raise ConfigError("No portainer configuration provided.")
    if not config.portainer.url:
        raise ConfigError("No portainer URL configured.")
    if not config.portainer.home_assistant_env:
        raise ConfigError(
            "No home assistant environment for portainer specified in .env.")
    # don't check whether version_to_update_to is greater than current one
    # with semver to allow forced downgrades
    if current_version != version_to_update_to:
        new_stack_content = re.sub(
            CURRENT_HASS_VERSION_REGEX,
            f"image: homeassistant/home-assistant:{version_to_update_to}",
            stack["stackFileContent"]
        )
        response = await client.get(
            config.portainer.url + "/api/endpoints",
            headers=portainer_headers)
        endpoints = response.json()
        try:
            pot_endpoints = filter(lambda e: e.get("Name", "").lower(
                # as it's actually checked for just a few lines above
            ) == config.portainer.home_assistant_env.lower(), endpoints)  # type: ignore
            endpoint = list(pot_endpoints)[0]
            endpoint_id = endpoint.get("Id", 0)
        except IndexError:
            return {
                "error": f"Environment '{config.portainer.home_assistant_env}' not found"
            }, 404
        try:
            response = await client.put(
                config.portainer.url +
                f"/api/stacks/{stack['Id']}?endpointId={endpoint_id}",
                json={"stackFileContent": new_stack_content},
                headers=portainer_headers
            )
            return {"success": True, "new_version": version_to_update_to}
        except Exception as error:
            if str(error) == "":
                return {"success": True, "new_version": version_to_update_to}
            raise Exception(
                f"Error applying new stack definition: {error}") from error
    return {"previous_version": current_version, "new_version": version_to_update_to}


async def update_home_assistant_with_portainer(config: Config):
    async with httpx.AsyncClient(verify=not config.portainer.insecure_https) as client:
        try:
            portainer_headers = await _log_in_to_portainer(config, client)
            stack = await _get_portainer_stack(config, client, portainer_headers)
            client.verify = not config.home_assistant.insecure_https
            current_version = _get_current_version_from_portainer_stack(stack)
            version_to_update_to = await _get_version_to_update_to(
                config,
                client,
                stack
            )
            return await _update_home_assistant_with_portainer(
                config,
                client,
                current_version,
                version_to_update_to,
                stack,
                portainer_headers
            )
        except Exception as exc:  # pylint: disable=broad-except
            return {"error": str(exc)}, 500


async def update_home_assistant_with_kubernetes(config: Config):
    kConfig = klient.Configuration()
    kConfig.host = config.kubernetes.url
    kConfig.verify_ssl = not config.kubernetes.insecure_https
    kConfig.api_key = {
        "authorization": f"Bearer {config.kubernetes.token}"}

    async with httpx.AsyncClient(verify=not config.home_assistant.insecure_https) as client:
        version_to_update_to = _get_version_to_update_to(config, client)

    kClient = klient.ApiClient(kConfig)
    appsV1 = klient.AppsV1Api(kClient)

    deploys = list(filter(lambda deploy: deploy.metadata.name == config.kubernetes.deployment_name,
                          appsV1.list_namespaced_deployment(config.kubernetes.namespace).items))
    if len(deploys) == 0:
        raise ValueError(
            f"Deployment {config.kubernetes.deployment_name} not found.")
    if len(deploys) > 1:
        raise ValueError("Multiple deployments with same name.")
    dep = deploys[0]
    dep.spec.template.spec.containers[
        0].image = f"homeassistant/home-assistant:{version_to_update_to}"
    appsV1.patch_namespaced_deployment(
        config.kubernetes.deployment_name, config.kubernetes.namespace, body=dep)


async def update_home_assistant(config: Config):
    if not config.home_assistant:
        raise ConfigError("No Home Assistant configuration provided.")
    try:
        if config.kubernetes.valid():
            return await update_home_assistant_with_kubernetes(config)
    except Exception as e:
        logging.error(e)
        logging.info("Falling back to portainer update mechanism.")
    if config.portainer.valid():
        return await update_home_assistant_with_portainer(config)
    raise ConfigError(
        "Neither Kubernetes nor Portainer configuration provided.")
