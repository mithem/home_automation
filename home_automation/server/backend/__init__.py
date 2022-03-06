"""A flask server hosting the backend API for managing docker containers.

Yes, I absolutely couldn't use Portainer!
(Well, I use it but this has more requirements.)"""
from typing import Dict, Tuple
import json
import os
import asyncio
import multiprocessing as mp
import re

import logging
import sqlite3
import semver
import docker
import httpx
from flask import Flask, render_template, request, url_for, redirect, escape
from docker.models.containers import Container as DockerContainer, Image as DockerImage
from docker.models.volumes import Volume as DockerVolume
from docker.errors import NotFound as ContainerNotFound, DockerException, APIError

import home_automation
from home_automation.server.backend.state_manager import StateManager
from home_automation.server.backend.version_manager import VersionManager


class ServerAPIError(Exception):
    """Any API error (that might be returned to the user)."""


DB_PATH = os.environ.get("DB_PATH", None)
if not DB_PATH:
    raise home_automation.config.ConfigError("DB_PATH envvar not found.")
if not os.path.isfile(DB_PATH):
    with open(DB_PATH, "w", encoding="utf-8"):
        pass

COMPOSE_FILE = os.environ.get("COMPOSE_FILE", None)
if COMPOSE_FILE and os.path.isdir(COMPOSE_FILE):
    COMPOSE_FILE = os.path.join(COMPOSE_FILE, "docker-compose.yml")

CLIENT, ERROR = None, None

INSECURE_HTTPS = os.environ.get("INSECURE_HTTPS", False)

PORTAINER_URL = os.environ.get("PORTAINER_URL", None)
PORTAINER_USER = os.environ.get("PORTAINER_USER", "admin")
PORTAINER_PASSWD = os.environ.get("PORTAINER_PASSWD", "")
PORTAINER_HOME_ASSISTANT_ENV = os.environ.get(
    "PORTAINER_HOME_ASSISTANT_ENV", "local")
PORTAINER_HOME_ASSISTANT_STACK = os.environ.get(
    "PORTAINER_HOME_ASSISTANT_STACK", None)

HASS_URL = os.environ.get("HASS_BASE_URL", None)
HASS_TOKEN = os.environ.get("HASS_TOKEN", None)

CURRENT_HASS_VERSION_REGEX = \
    r"image: homeassistant/home-assistant:(?P<version>\d\d\d\d\.\d\d?\.\d+)"
PORTAINER_CALLS_TIMEOUT = 5


def try_reloading_client():
    """Try reloading/reconnecting the docker client and save error if appropriate."""
    global CLIENT, ERROR  # pylint: disable=global-statement
    try:
        CLIENT = docker.from_env()
    except DockerException as docker_exception:
        ERROR = docker_exception


try_reloading_client()


def compose_pull_exec():
    """Compose pull, blocking."""
    os.system(f"docker-compose -f '{COMPOSE_FILE}' pull")
    state_manager = StateManager(DB_PATH)
    state_manager.update_status("pulling", False)


def compose_up_exec():
    """"Compose up, blocking."""
    os.system(f"docker-compose -f '{COMPOSE_FILE}' up -d")
    state_manager = StateManager(DB_PATH)
    state_manager.update_status("upping", False)


def compose_down_exec():
    """Compose down, blocking."""
    os.system(f"docker-compose -f '{COMPOSE_FILE}' down")
    state_manager = StateManager(DB_PATH)
    state_manager.update_status("downing", False)


def docker_prune_exec():
    """Docker prune, blocking."""
    os.system("docker system prune -af")
    state_manager = StateManager(DB_PATH)
    state_manager.update_status("pruning", False)


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


def create_app(options=None):  # pylint: disable=too-many-locals, too-many-statements
    """App factory."""
    app = Flask(__name__)
    state_manager = StateManager(DB_PATH)
    version_manager = VersionManager(DB_PATH)
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
            return str(ERROR), 500
        except (APIError, Exception) as exc:  # pylint: disable=broad-except
            # originally a docker error, but
            # docker might also raise other exceptions like some from requests
            try_reloading_client()
            return str(exc), 500

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
        if not PORTAINER_URL:
            raise ServerAPIError("No portainer URL configured.")
        payload = {"username": PORTAINER_USER, "password": PORTAINER_PASSWD}
        response = await client.post(
            PORTAINER_URL + "/api/auth",
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
        if not PORTAINER_URL:
            raise ServerAPIError("No portainer URL configured.")
        if not PORTAINER_HOME_ASSISTANT_STACK:
            raise ServerAPIError(
                "No portainer stack defining home assistant configured in env.")
        response = await client.get(PORTAINER_URL + "/api/stacks",
                                    headers=headers,
                                    timeout=PORTAINER_CALLS_TIMEOUT)
        stacks = response.json()
        try:
            pot_stacks = filter(lambda s: s.get("Name", "").lower(
            ) == PORTAINER_HOME_ASSISTANT_STACK.lower(), stacks)  # type: ignore
            # as it's actually checked for just a few lines above
            stack = list(pot_stacks)[0]
            stack_id = stack.get("Id", None)
            if not stack_id:
                raise ServerAPIError("Invalid data received from portainer.")
            response = await client.get(
                PORTAINER_URL + f"/api/stacks/{stack_id}/file",
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
                f"Stack '{PORTAINER_HOME_ASSISTANT_STACK}' not found.") from err

    async def _get_version_to_update_to(
        client: httpx.AsyncClient,
        stack: Dict[str, str]
    ) -> Tuple[str, str]:
        """Get current version as well as version of home assistant to update to (as a tuple).
        Might throw ServerAPIError."""
        if not HASS_URL:
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
            hass_headers = {"authorization": f"Bearer {HASS_TOKEN}"}
            response = await client.get(
                HASS_URL + "/api/states/sensor.docker_hub",
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
    ) -> Tuple[Dict[str, str], int]:
        if not PORTAINER_URL:
            raise ServerAPIError("No portainer URL configured.")
        if not PORTAINER_HOME_ASSISTANT_ENV:
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
                PORTAINER_URL + "/api/endpoints",
                headers=portainer_headers)
            endpoints = response.json()
            try:
                pot_endpoints = filter(lambda e: e.get("Name", "").lower(
                ) == PORTAINER_HOME_ASSISTANT_ENV.lower(), endpoints)
                endpoint = list(pot_endpoints)[0]
                endpoint_id = endpoint.get("Id", 0)
            except IndexError:
                return {"error": f"Environment '{PORTAINER_HOME_ASSISTANT_ENV}' not found"}, 404
            try:
                response = await client.put(
                    PORTAINER_URL +
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
        if not HASS_URL:
            return {"error": "No home assistant URL defined."}, 500
        if not HASS_TOKEN:
            return {"error": "No home assistant token defined."}, 401
        async with httpx.AsyncClient(verify=not INSECURE_HTTPS) as client:
            try:
                portainer_headers = await _log_in_to_portainer(client)
                stack = await _get_portainer_stack(client, portainer_headers)
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
    return app
