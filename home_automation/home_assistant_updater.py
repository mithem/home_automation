"""Everything responsible for updating home assistant (except the API)"""
import asyncio
import logging
import re
from typing import Any, Dict, Optional, Tuple, Union

import httpx
from kubernetes import client as klient

from home_automation import utilities
from home_automation.config import Config, ConfigError, load_config

PORTAINER_CALLS_TIMEOUT = 5
CURRENT_HASS_VERSION_REGEX = (
    r"image: homeassistant/home-assistant:(?P<version>\d\d\d\d\.\d\d?\.\d+)"
)


class UpdaterError(Exception):
    """Any error specific to home_assistant_updater"""


async def _log_in_to_portainer(
    config: Config, client: httpx.AsyncClient
) -> Dict[str, str]:
    """Log in to portainer and return authorization header. Might raise ServerAPIError."""
    if not config.portainer:
        raise ConfigError("No portainer configuration provided.")
    if not config.portainer.url:
        raise ConfigError("No portainer URL configured.")
    payload = {
        "username": config.portainer.username,
        "password": config.portainer.password,
    }
    response = await client.post(
        config.portainer.url + "/api/auth",
        json=payload,
        timeout=PORTAINER_CALLS_TIMEOUT,
    )
    auth_data = response.json()
    jwt = auth_data.get("jwt", None)
    if not jwt:
        raise PermissionError("Forbidden (portainer credentials).")
    return {"authorization": f"Bearer {jwt}"}


async def _get_portainer_stack(
    config: Config, client: httpx.AsyncClient, headers: Dict[str, str]
) -> Dict[str, str]:
    """Get portainer stack data. Might raise ServerAPIError."""
    if not config.portainer:
        raise ConfigError("No portainer configuration provided.")
    if not config.portainer.url:
        raise ConfigError("No portainer URL configured.")
    if not config.home_assistant.portainer:
        raise ConfigError("No portainer configuration for home_assistant found.")
    response = await client.get(
        config.portainer.url + "/api/stacks",
        headers=headers,
        timeout=PORTAINER_CALLS_TIMEOUT,
    )
    stacks = response.json()
    try:

        def filter_stacks(
            stack: Dict[str, str]
        ) -> bool:  # pylint: disable=missing-function-docstring
            # config.home_assistant.portainer already asserted to exist above
            return stack.get("Name") == config.home_assistant.portainer.stack  # type: ignore

        pot_stacks = filter(filter_stacks, stacks)
        stack = list(pot_stacks)[0]
        stack_id = stack.get("Id", None)
        if not stack_id:
            raise UpdaterError("Invalid data received from portainer.")
        response = await client.get(
            config.portainer.url + f"/api/stacks/{stack_id}/file",
            headers=headers,
            timeout=PORTAINER_CALLS_TIMEOUT,
        )
        stack_data = response.json()
        file_content = stack_data.get("StackFileContent", None)
        if not file_content:
            raise UpdaterError("No StackFileContent provided from portainer.")
        stack["stackFileContent"] = file_content
        return stack
    except IndexError as err:
        raise UpdaterError(
            f"Stack '{config.home_assistant.portainer.stack}' not found."
        ) from err


def _get_current_version_from_portainer_stack(stack: Dict[str, str]):
    """Get current home assistant version from stack definition."""
    result = re.search(CURRENT_HASS_VERSION_REGEX, stack["stackFileContent"])
    if not result:
        raise UpdaterError("Could not extract version information from stack info.")
    current_version = result.groupdict().get("version", None)
    return current_version


async def _get_version_to_update_to(
    config: Config,
    client: httpx.AsyncClient,
    user_payload: Optional[Dict[str, str]] = None,
) -> str:
    """Get version of home assistant to update to. Might throw ServerAPIError."""
    if not config.home_assistant:
        raise ConfigError("No Home Assistant configuration provided.")
    if not config.home_assistant.url:
        raise ConfigError("No home assistant URL configured.")
    version_to_update_to = None
    if user_payload:
        if isinstance(user_payload, dict):
            version_to_update_to = user_payload.get("update_to_version", None)
    if not version_to_update_to:
        hass_headers = {"authorization": f"Bearer {config.home_assistant.token}"}
        response = await client.get(
            config.home_assistant.url + "/api/states/sensor.docker_hub",
            headers=hass_headers,
            timeout=PORTAINER_CALLS_TIMEOUT,
        )
        data = response.json()
        version_to_update_to = data.get("state", None)
    if not version_to_update_to:
        raise UpdaterError(
            "Could not retreive newest available version from home assistant."
        )
    return version_to_update_to


async def _update_home_assistant_with_portainer(  # pylint: disable=too-many-arguments
    config: Config,
    client: httpx.AsyncClient,
    current_version: str,
    version_to_update_to: str,
    stack: Dict[str, str],
    portainer_headers: Dict[str, str],
) -> Union[Tuple[Dict[str, Any], int], Dict[str, Any]]:
    if not config.portainer:
        raise ConfigError("No portainer configuration provided.")
    if not config.portainer.url:
        raise ConfigError("No portainer URL configured.")
    assert (
        config.home_assistant.portainer
    ), "No portainer configuration for home_assistant found."
    # don't check whether version_to_update_to is greater than current one
    # with semver to allow forced downgrades
    if current_version != version_to_update_to:
        new_stack_content = re.sub(
            CURRENT_HASS_VERSION_REGEX,
            f"image: homeassistant/home-assistant:{version_to_update_to}",
            stack["stackFileContent"],
        )
        response = await client.get(
            config.portainer.url + "/api/endpoints", headers=portainer_headers
        )
        endpoints = response.json()
        try:

            def filter_endpoints(
                endpoint: Dict[str, str]
            ) -> bool:  # pylint: disable=missing-function-docstring
                # config.home_assistant.portainer already asserted to exist above
                return (
                    endpoint.get("Name")
                    == config.home_assistant.portainer.environment  # type: ignore
                )

            pot_endpoints = filter(filter_endpoints, endpoints)
            endpoint = list(pot_endpoints)[0]
            endpoint_id = endpoint.get("Id", 0)
        except IndexError:
            return {
                "error": f"Environment '{config.home_assistant.portainer.environment}' not found"
            }, 404
        try:
            response = await client.put(
                config.portainer.url
                + f"/api/stacks/{stack['Id']}?endpointId={endpoint_id}",
                json={"stackFileContent": new_stack_content},
                headers=portainer_headers,
            )
            return {"success": True, "new_version": version_to_update_to}
        except Exception as error:
            logging.error(error)
            if str(error) == "":
                return {"success": True, "new_version": version_to_update_to}
            raise Exception(f"Error applying new stack definition: {error}") from error
    return {"previous_version": current_version, "new_version": version_to_update_to}


async def update_home_assistant_with_portainer(config: Config):
    """Use portainer to update Home Assistant."""
    try:
        async with httpx.AsyncClient(
            verify=not config.portainer.insecure_https
        ) as client:
            portainer_headers = await _log_in_to_portainer(config, client)
            stack = await _get_portainer_stack(config, client, portainer_headers)
        async with httpx.AsyncClient(
            verify=not config.home_assistant.insecure_https
        ) as client:
            current_version = _get_current_version_from_portainer_stack(stack)
            version_to_update_to = await _get_version_to_update_to(
                config, client, stack
            )
            return await _update_home_assistant_with_portainer(
                config,
                client,
                current_version,
                version_to_update_to,
                stack,
                portainer_headers,
            )
    except Exception as exc:  # pylint: disable=broad-except
        logging.error(exc)
        return {"error": str(exc)}, 500


async def update_home_assistant_with_kubernetes(config: Config):
    """Use kubernetes to update Home Assistant."""
    if not config.home_assistant.deployment:
        raise ConfigError(
            "No home_assistant.deployment configuration (for k8s) provided."
        )
    k_client = utilities.get_k8s_client(config)
    apps_v1 = klient.AppsV1Api(k_client)

    async with httpx.AsyncClient(
        verify=not config.home_assistant.insecure_https
    ) as client:
        version_to_update_to = await _get_version_to_update_to(config, client)

    def filter_deploys(
        deploy: klient.V1Deployment,
    ) -> bool:  # pylint: disable=missing-function-docstring
        # config.home_assistant.portainer already asserted to exist above
        return deploy.metadata.name == config.home_assistant.deployment.name  # type: ignore

    deploys = list(
        filter(
            filter_deploys,
            apps_v1.list_namespaced_deployment(
                config.home_assistant.deployment.namespace
            ).items,
        )
    )
    if len(deploys) == 0:
        raise ValueError(
            f"Deployment {config.home_assistant.deployment.name} not found."
        )
    if len(deploys) > 1:
        raise ValueError("Multiple deployments with same name.")
    dep = deploys[0]
    dep.spec.template.spec.containers[
        0
    ].image = f"homeassistant/home-assistant:{version_to_update_to}"
    apps_v1.patch_namespaced_deployment(
        config.home_assistant.deployment.name,
        config.home_assistant.deployment.namespace,
        body=dep,
    )


async def update_home_assistant(config: Config):
    """Update Home Assistant."""
    if not config.home_assistant:
        raise ConfigError("No Home Assistant configuration provided.")
    try:
        if config.kubernetes.valid():
            return await update_home_assistant_with_kubernetes(config)
        if config.portainer.valid():
            return await update_home_assistant_with_portainer(config)
        raise ConfigError("Neither Kubernetes nor Portainer configuration provided.")
    except Exception as error:  # pylint: disable=broad-except
        logging.error(error)
        return {"error": str(error)}, 500


async def main():
    """Main entrypoint for just updating HomeAssistant (standalone)."""
    config = load_config()
    await update_home_assistant(config)


if __name__ == "__main__":
    asyncio.run(main())
