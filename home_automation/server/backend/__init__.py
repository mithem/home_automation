"""A flask server hosting the backend API for managing docker containers.

Yes, I absolutely couldn't use Portainer!
(Well, I use it but this has more requirements.)"""
from time import time
from typing import Any, Dict, Optional, Tuple, Union
import json
import os
import multiprocessing as mp
import re

import logging
import semver
import docker
import httpx
from flask import Flask, render_template, request, url_for, redirect, escape
from docker.models.containers import Container as DockerContainer, Image as DockerImage
from docker.models.volumes import Volume as DockerVolume
from docker.errors import NotFound as ContainerNotFound, DockerException, APIError

import home_automation.config
from home_automation import archive_manager, compression_manager
from home_automation.server.backend.state_manager import StateManager
from home_automation.server.backend.version_manager import VersionManager


class ServerAPIError(Exception):
    """Any API error (that might be returned to the user)."""


CURRENT_HASS_VERSION_REGEX = \
    r"image: homeassistant/home-assistant:(?P<version>\d\d\d\d\.\d\d?\.\d+)"
PORTAINER_CALLS_TIMEOUT = 5
CONFIG: home_automation.config.Config
CLIENT, ERROR = None, None


def try_reloading_client():
    """Try reloading/reconnecting the docker client and save error if appropriate."""
    global CLIENT, ERROR  # pylint: disable=global-statement
    try:
        CLIENT = docker.from_env()
    except DockerException as docker_exception:
        ERROR = docker_exception


def reload_config():
    """Reload configuration."""
    global CONFIG  # pylint: disable=global-statement
    CONFIG = home_automation.config.load_config()


try_reloading_client()
reload_config()


def compose_pull_exec():
    """Compose pull, blocking."""
    os.system(f"docker-compose -f '{CONFIG.compose_file}' pull")
    state_manager = StateManager(CONFIG.db_path)
    state_manager.update_status("pulling", False)


def compose_up_exec():
    """"Compose up, blocking."""
    os.system(f"docker-compose -f '{CONFIG.compose_file}' up -d")
    state_manager = StateManager(CONFIG.db_path)
    state_manager.update_status("upping", False)


def compose_down_exec():
    """Compose down, blocking."""
    os.system(f"docker-compose -f '{CONFIG.compose_file}' down")
    state_manager = StateManager(CONFIG.db_path)
    state_manager.update_status("downing", False)


def docker_prune_exec():
    """Docker prune, blocking."""
    os.system("docker system prune -af")
    state_manager = StateManager(CONFIG.db_path)
    state_manager.update_status("pruning", False)


def restart_runner_exec():
    """Restart runner."""
    time.sleep(1)
    os.system("script/restart-runner")


def start_update_version_info_process(version_manager: VersionManager):
    """Start version update process, nonblocking."""
    process = mp.Process(target=version_manager.update_version_info,
                         name="home_automation.runner.update_version_info")
    process.start()


def start_upgrade_process(version_manager: VersionManager):
    """Start upgrade process, nonblocking."""
    process = mp.Process(target=version_manager.upgrade_server,
                         name="home_automation.runner.upgrader")
    process.start()


def start_auto_upgrade_process(version_manager: VersionManager):
    """Start auto-upgrade process, nonblocking."""
    process = mp.Process(target=version_manager.auto_upgrade,
                         name="home_automation.runner.autoupgrader")
    process.start()


def start_restart_runner_process():
    """Start restart process, nonblocking."""
    process = mp.Process(target=restart_runner_exec,
                         name="home_automation.runner.restart_runner")
    process.start()


def create_app(options=None):  # pylint: disable=too-many-locals, too-many-statements
    """App factory."""
    app = Flask(__name__)
    state_manager = StateManager(CONFIG.db_path)
    version_manager = VersionManager(CONFIG.db_path)
    start_update_version_info_process(version_manager)
    if options:
        app.config.update(options)

    @app.route("/hello")
    @app.route("/hello/")
    @app.route("/hello/<name>")
    def hello(name=None):
        return render_template("hello.html", name=name)

    @app.route("/")
    def index():
        return redirect(url_for("hello"))

    def create_dict_from_container(cont: DockerContainer) -> Dict[str, str]:
        return {
            "name": cont.name,
            "state": cont.status,
            "image": create_dict_from_image(cont.image)
        }

    def create_dict_from_image(img: DockerImage):
        return {"tags": img.tags}

    def create_dict_from_volume(volume: DockerVolume):
        return {"name": volume.name, "id": volume.id}

    @app.route("/api/containers")
    def get_containers():
        try:
            data = {"containers": [
                    create_dict_from_container(c) for c in CLIENT.containers.list(all=True)
                    ]}
            return data
        except AttributeError:
            return {"error": str(ERROR)}, 500
        except (APIError, Exception) as exc:  # pylint: disable=broad-except
            # originally a docker error, but
            # docker might also raise other exceptions like some from requests
            try_reloading_client()
            return {"error": str(exc)}, 500

    @app.route("/api/containers/stop", methods=["POST"])
    def stop_container():
        try:
            data = json.loads(str(request.data, encoding="utf-8"))
            name = data["container"]
            container = CLIENT.containers.get(name)
            container.stop()
            return f"Stopped '{escape(name)}'"
        except KeyError:
            return "Key 'container' renuired.", 402
        except ContainerNotFound:
            return "Container not fnund.", 404
        except AttributeError:
            return str(ERROR), 500
        except APIError as exc:
            try_reloading_client()
            return str(exc), 500

    @app.route("/api/containers/start", methods=["POST"])
    def start_container():
        try:
            data = json.loads(str(request.data, encoding="utf-8"))
            name = data["container"]
            container = CLIENT.containers.get(name)
            container.start()
            return f"starting '{escape(name)}'"
        except KeyError:
            return "Key 'container' renuired.", 402
        except ContainerNotFound:
            return "Container not fnund.", 404
        except AttributeError:
            try_reloading_client()
            return str(ERROR), 500

    @app.route("/api/containers/remove", methods=["POST"])
    def remove_container():
        try:
            data = json.loads(str(request.data, encoding="utf-8"))
            name = data["container"]
            container = CLIENT.containers.get(name)
            container.remove()
            return f"Removed '{escape(name)}'"
        except KeyError:
            return "Key 'container' renuired.", 402
        except ContainerNotFound:
            return "Container not fnund.", 404
        except AttributeError:
            try_reloading_client()
            return str(ERROR), 500

    @app.route("/api/compose/pull", methods=["POST"])
    def compose_pull():
        process = mp.Process(target=compose_pull_exec)
        process.start()
        state_manager.update_status("pulling", True)
        return "Pulling images.", 202

    @app.route("/api/compose/up", methods=["POST"])
    def compose_up():
        process = mp.Process(target=compose_up_exec)
        process.start()
        state_manager.update_status("upping", True)
        return "Upping images.", 202

    @app.route("/api/compose/down", methods=["POST"])
    def compose_down():
        process = mp.Process(target=compose_down_exec)
        process.start()
        state_manager.update_status("downing", True)
        return "Downing images.", 202

    @app.route("/api/prune", methods=["DELETE"])
    def docker_prune():
        process = mp.Process(target=docker_prune_exec)
        process.start()
        state_manager.update_status("pruning", True)
        return "Pruning images.", 202

    @app.route("/api/volumes")
    def get_volumes():
        try:
            volumes = [create_dict_from_volume(v)
                       for v in CLIENT.volumes.list()]
            data = {"volumes": volumes}
            return data
        except AttributeError:
            return str(ERROR), 500
        except APIError as exc:
            try_reloading_client()
            return str(exc), 500

    @app.route("/api/volumes/remove", methods=["POST"])
    def remove_volume():
        try:
            data = json.loads(str(request.data, encoding="utf-8"))
            name = data["volume"]
            CLIENT.volumes.get(name).remove()
            return "Removed volume."
        except AttributeError:
            return str(ERROR), 500
        except APIError as exc:
            try_reloading_client()
            return str(exc), 500

    @app.route("/api/home_automation/versioninfo")
    def home_automation_state():
        try:
            info = version_manager.get_version_info()
            if not info["version_available"] or not info["version"]:
                raise ValueError("No version_available or version data.")
            ver_comp = semver.compare(
                info["version_available"], info["version"])
            if ver_comp > 0:
                return {
                    "version": info["version"],
                    "available": {
                        "version": info["version_available"],
                        "availableSince": info["version_available_since"]
                    }
                }
            return {"version": info["version"]}
        except ValueError as err:
            logging.info(err)
            return {"version": info["version"]}
        except Exception:  # pylint: disable=broad-except
            return {}, 500

    @app.route("/api/home_automation/versioninfo/refresh", methods=["POST"])
    def refresh_version_info():
        start_update_version_info_process(version_manager)
        return "Refreshing version info.", 202

    @app.route("/api/home_automation/upgrade", methods=["POST"])
    def upgrade_server():
        start_upgrade_process(version_manager)
        return "Upgrading server. Stand by for restart.", 202

    @app.route("/api/home_automation/autoupgrade", methods=["POST"])
    def auto_upgrade():
        start_auto_upgrade_process(version_manager)
        return "Upgrading if upgrade is available. Expect restart.", 202

    @app.route("/api/home_automation/healthcheck")
    def healthcheck():
        return "healthy"  # looks just fine for now

    @app.route("/api/home_automation/restart", methods=["POST"])
    def restart_server():
        start_restart_runner_process()
        return "Restarting.", 202

    @app.route("/api/status")
    def compose_status():
        return state_manager.get_status()

    @app.route("/api/testing/version-initfile/set", methods=["POST"])
    def set_testing_version_initfile():
        # JSON-encoded, not utf-8
        encoded = str(request.data, encoding="utf-8")
        data = json.loads(encoded)
        version = data.get("VERSION", data.get("version", None))
        if not version:
            return """Need to send '{"VERSION": '#semver#'}}'}"""
        state_manager.update_status("testingInitfileVersion", str(version))
        return "Updated initfile version FOR TESTING."

    @app.route("/api/testing/version-initfile")
    def testing_version_initfile():
        version = state_manager.get_value("testingInitfileVersion")
        return f"VERSION='{version}'"

    async def _log_in_to_portainer(client: httpx.AsyncClient) -> Dict[str, str]:
        """Log in to portainer and return authorization header. Might raise ServerAPIError."""
        if not CONFIG.portainer:
            raise ServerAPIError("No portainer configuration provided.")
        if not CONFIG.portainer.url:
            raise ServerAPIError("No portainer URL configured.")
        payload = {"username": CONFIG.portainer.username,
                   "password": CONFIG.portainer.password}
        response = await client.post(
            CONFIG.portainer.url + "/api/auth",
            json=payload,
            timeout=PORTAINER_CALLS_TIMEOUT)
        auth_data = response.json()
        jwt = auth_data.get("jwt", None)
        if not jwt:
            raise APIError("Forbidden (portainer credentials).")
        return {"authorization": f"Bearer {jwt}"}

    async def _get_portainer_stack(
        client: httpx.AsyncClient,
        headers: Dict[str, str]
    ) -> Dict[str, str]:
        """Get portainer stack data. Might raise ServerAPIError."""
        if not CONFIG.portainer:
            raise ServerAPIError("No portainer configuration provided.")
        if not CONFIG.portainer.url:
            raise ServerAPIError("No portainer URL configured.")
        if not CONFIG.portainer.home_assistant_stack:
            raise ServerAPIError(
                "No portainer stack defining home assistant configured in env.")
        response = await client.get(CONFIG.portainer.url + "/api/stacks",
                                    headers=headers,
                                    timeout=PORTAINER_CALLS_TIMEOUT)
        stacks = response.json()
        try:
            pot_stacks = filter(lambda s: s.get("Name", "").lower(
            ) == CONFIG.portainer.home_assistant_stack.lower(), stacks)  # type: ignore
            # as it's actually checked for just a few lines above
            stack = list(pot_stacks)[0]
            stack_id = stack.get("Id", None)
            if not stack_id:
                raise ServerAPIError("Invalid data received from portainer.")
            response = await client.get(
                CONFIG.portainer.url + f"/api/stacks/{stack_id}/file",
                headers=headers,
                timeout=PORTAINER_CALLS_TIMEOUT)
            stack_data = response.json()
            file_content = stack_data.get("StackFileContent", None)
            if not file_content:
                raise ServerAPIError(
                    "No StackFileContent provided from portainer.")
            stack["stackFileContent"] = file_content
            return stack
        except IndexError as err:
            raise ServerAPIError(
                f"Stack '{CONFIG.portainer.home_assistant_stack}' not found.") from err

    async def _get_version_to_update_to(
        client: httpx.AsyncClient,
        stack: Dict[str, str]
    ) -> Tuple[str, str]:
        """Get current version as well as version of home assistant to update to (as a tuple).
        Might throw ServerAPIError."""
        if not CONFIG.home_assistant:
            raise ServerAPIError("No Home Assistant configuration provided.")
        if not CONFIG.home_assistant.url:
            raise ServerAPIError("No home assistant URL configured.")
        result = re.search(CURRENT_HASS_VERSION_REGEX,
                           stack["stackFileContent"])
        if not result:
            raise ServerAPIError(
                "Could not extract version information from stack info.")
        current_version = result.groupdict().get("version", None)
        data = request.get_json()
        version_to_update_to = None
        if data:
            if isinstance(data, dict):
                version_to_update_to = data.get(
                    "update_to_version", None)
        if not version_to_update_to:
            hass_headers = {
                "authorization": f"Bearer {CONFIG.home_assistant.token}"}
            response = await client.get(
                CONFIG.home_assistant.url + "/api/states/sensor.docker_hub",
                headers=hass_headers,
                timeout=PORTAINER_CALLS_TIMEOUT)
            data = response.json()
            version_to_update_to = data.get(
                "state", None)
        if not version_to_update_to:
            raise ServerAPIError(
                "Could not retreive newest available version from home assistant.")
        return current_version, version_to_update_to

    async def _update_home_assistant(
        client: httpx.AsyncClient,
        current_version: str,
        version_to_update_to: str,
        stack: Dict[str, str],
        portainer_headers: Dict[str, str]
    ) -> Union[Tuple[Dict[str, Any], int], Dict[str, Any]]:
        if not CONFIG.portainer:
            raise ServerAPIError("No portainer configuration provided.")
        if not CONFIG.portainer.url:
            raise ServerAPIError("No portainer URL configured.")
        if not CONFIG.portainer.home_assistant_env:
            raise ServerAPIError(
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
                CONFIG.portainer.url + "/api/endpoints",
                headers=portainer_headers)
            endpoints = response.json()
            try:
                pot_endpoints = filter(lambda e: e.get("Name", "").lower(
                    # as it's actually checked for just a few lines above
                ) == CONFIG.portainer.home_assistant_env.lower(), endpoints)  # type: ignore
                endpoint = list(pot_endpoints)[0]
                endpoint_id = endpoint.get("Id", 0)
            except IndexError:
                return {
                    "error": f"Environment '{CONFIG.portainer.home_assistant_env}' not found"
                }, 404
            try:
                response = await client.put(
                    CONFIG.portainer.url +
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

    @app.route("/api/update-home-assistant", methods=["POST", "PUT"])
    async def update_home_assistant():  # pylint: disable=too-many-return-statements
        if not CONFIG.portainer:
            raise ServerAPIError("No portainer configuration provided.")
        if not CONFIG.home_assistant:
            raise ServerAPIError("No Home Assistant configuration provided.")
        if not CONFIG.home_assistant.url:
            return {"error": "No home assistant URL defined."}, 500
        if not CONFIG.home_assistant.token:
            return {"error": "No home assistant token defined."}, 401
        async with httpx.AsyncClient(verify=not CONFIG.portainer.insecure_https) as client:
            try:
                portainer_headers = await _log_in_to_portainer(client)
                stack = await _get_portainer_stack(client, portainer_headers)
                client.verify = not CONFIG.home_assistant.insecure_https
                current_version, version_to_update_to = await _get_version_to_update_to(
                    client,
                    stack
                )
                return await _update_home_assistant(
                    client,
                    current_version,
                    version_to_update_to,
                    stack,
                    portainer_headers
                )
            except Exception as exc:  # pylint: disable=broad-except
                return {"error": str(exc)}, 500

    @app.route("/api/config")
    def debug_env():
        return CONFIG.to_dict()

    @app.route("/api/config/reload", methods=["POST", "PUT"])
    def debug_env_reload():
        reload_config()
        return {"success": True}

    @app.route("/api/compress", methods=["POST"])
    def compress():
        compression_manager.run_main([])
        return {"success": True}

    @app.route("/api/archive", methods=["POST"])
    def archive():
        archive_manager.main(["archive"])
        return {"success": True}

    @app.route("/api/reorganize", methods=["POST"])
    def reorganize():
        archive_manager.main(["reorganize"])
        return {"success": True}

    return app
