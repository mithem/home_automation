"""A flask server hosting the backend API for managing docker containers.

Yes, I absolutely couldn't use Portainer!
(Well, I use it but this has more requirements.)"""
from typing import Dict
import json
import os
import time
import multiprocessing as mp

import logging
import semver
import docker
import httpx
import oauthlib.oauth2.rfc6749.errors
from flask import Flask, render_template, request, url_for, redirect, escape
from docker.models.containers import Container as DockerContainer, Image as DockerImage
from docker.models.volumes import Volume as DockerVolume
from docker.errors import NotFound as ContainerNotFound, DockerException, APIError
from google.auth.transport.requests import Request
import google.auth.exceptions
from google.oauth2.credentials import Credentials

from home_automation import config as haconfig
from home_automation import archive_manager, compression_manager
from home_automation.server.backend.state_manager import StateManager
from home_automation.server.backend.version_manager import VersionManager
import home_automation.utilities
import home_automation.home_assistant_updater
from home_automation.server.backend import oauth2_helpers
from home_automation import frontend_deployer


class ServerAPIError(Exception):
    """Any API error (that might be returned to the user)."""


CONFIG: haconfig.Config
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
    CONFIG = haconfig.load_config()


try_reloading_client()
reload_config()


def compose_pull_exec():
    """Compose pull, blocking."""
    os.system(f"docker-compose -f '{CONFIG.compose_file}' pull")
    state_manager = StateManager(CONFIG.db_path)
    state_manager.update_status("pulling", False)


def compose_up_exec():
    """ "Compose up, blocking."""
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
    process = mp.Process(
        target=version_manager.update_version_info,
        name="home_automation.runner.update_version_info",
    )
    process.start()


def start_upgrade_process(version_manager: VersionManager):
    """Start upgrade process, nonblocking."""
    process = mp.Process(
        target=version_manager.upgrade_server, name="home_automation.runner.upgrader"
    )
    process.start()


def start_auto_upgrade_process(version_manager: VersionManager):
    """Start auto-upgrade process, nonblocking."""
    process = mp.Process(
        target=version_manager.auto_upgrade, name="home_automation.runner.autoupgrader"
    )
    process.start()


def start_restart_runner_process():
    """Start restart process, nonblocking."""
    process = mp.Process(
        target=restart_runner_exec, name="home_automation.runner.restart_runner"
    )
    process.start()


def start_frontend_build_process():
    """Start frontend build process, nonblocking."""
    process = mp.Process(
        target=frontend_deployer.build_image,
        name="home_automation.runner.build_frontend",
        args=(CONFIG,),
    )
    process.start()


def start_frontend_deploy_process():
    """Start frontend deploy process, nonblocking."""
    process = mp.Process(
        target=frontend_deployer.build_and_deploy_frontend,
        name="home_automation.runner.deploy_frontend",
        args=(CONFIG,),
    )
    process.start()


def create_app(options=None):  # pylint: disable=too-many-locals, too-many-statements
    """App factory."""
    app = Flask(__name__)
    state_manager = StateManager(CONFIG)
    version_manager = VersionManager(CONFIG)
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
            "image": create_dict_from_image(cont.image),
        }

    def create_dict_from_image(img: DockerImage):
        return {"tags": img.tags}

    def create_dict_from_volume(volume: DockerVolume):
        return {"name": volume.name, "id": volume.id}

    @app.route("/api/containers")
    def get_containers():
        try:
            data = {
                "containers": [
                    create_dict_from_container(c)
                    for c in CLIENT.containers.list(all=True)
                ]
            }
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
            volumes = [create_dict_from_volume(v) for v in CLIENT.volumes.list()]
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
            if not info.get("version_available") or not info.get("version"):
                raise ValueError("No version_available or version data.")
            ver_comp = semver.compare(
                info.get("version_available"), info.get("version")
            )
            if ver_comp > 0:
                return {
                    "version": info.get("version"),
                    "available": {
                        "version": info.get("version_available"),
                        "availableSince": info.get("version_available_since"),
                    },
                }
            return {"version": info.get("version")}
        except ValueError as err:
            logging.info(err)
            return {"version": info.get("version")}
        except Exception as err:  # pylint: disable=broad-except
            logging.error(err)
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

    @app.route("/api/status", methods=["GET", "DELETE"])
    def compose_status():
        if request.method == "GET":
            return state_manager.get_status()
        if request.method == "DELETE":
            state_manager.reset_status()
            return "Status reset."
        return "Method not allowed.", 405

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

    @app.route("/api/update-home-assistant", methods=["POST", "PUT"])
    async def update_home_assistant():  # pylint: disable=too-many-return-statements
        if not CONFIG.home_assistant:
            raise ServerAPIError("No Home Assistant configuration provided.")
        if not CONFIG.home_assistant.url:
            return {"error": "No home assistant URL defined."}, 500
        if not CONFIG.home_assistant.token:
            return {"error": "No home assistant token defined."}, 401
        try:
            await home_automation.home_assistant_updater.update_home_assistant(CONFIG)
            return {"success": True}
        except Exception as error:  # pylint: disable=broad-except
            logging.error(error)
            return {"error": str(error)}, 500

    @app.route("/api/config")
    def debug_env():
        return CONFIG.to_dict()

    @app.route("/api/config/reload", methods=["POST", "PUT"])
    def debug_env_reload():
        reload_config()
        return {"success": True}

    @app.route("/api/compress", methods=["POST"])
    async def compress():
        await compression_manager.compress(CONFIG)
        return {"success": True}

    @app.route("/api/archive", methods=["POST"])
    def archive():
        archive_manager.archive(CONFIG)
        return {"success": True}

    @app.route("/api/reorganize", methods=["POST"])
    def reorganize():
        archive_manager.reorganize(CONFIG)
        return {"success": True}

    @app.route("/api/mail/test", methods=["POST"])
    def mail_test():
        creds = oauth2_helpers.get_google_oauth2_credentials(state_manager)
        try:
            home_automation.utilities.send_mail(
                creds, "Test", "This is a test mail sent from home_automation."
            )
            return {"success": True}
        except google.auth.exceptions.RefreshError as error:
            if "credentials do not contain the necessary fields" in str(error):
                state_manager.update_status("test_email_pending", True)
                return "Unauthorized.", 401
            return str(error), 401

    @app.route("/backend/home_automation/oauth2/google/callback")
    def google_oauth2_callback():
        authorization_response = request.url
        flow = oauth2_helpers.get_oauth_flow(CONFIG)
        print(authorization_response)
        print(flow)
        try:
            flow.fetch_token(authorization_response=authorization_response)
        except oauthlib.oauth2.rfc6749.errors.InvalidGrantError:
            return "Invalid grant.", 500
        except oauthlib.oauth2.rfc6749.errors.InsecureTransportError:
            error = "InsecureTransportError. Consider configuring home_automation.api_server to \
use ssl in order to meet the requirements for OAuth2 (.ssl_cert_path & .ssl_key_path respectively)."
            return render_template("error.html", error=error), 500
        oauth2_helpers.save_credentials(flow.credentials, state_manager)
        pending = bool(int(state_manager.get_value("test_email_pending")))
        if pending:
            state_manager.update_status("test_email_pending", False)
            mail_test()
        return render_template("oauth2-credentials-saved-successfully.html")

    @app.route("/backend/home_automation/oauth2/google/request")
    def request_google_oauth2_auth():
        creds = None
        # The file token.json stores the user"s access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file(
                "token.json", oauth2_helpers.GOOGLE_MAIL_SEND_SCOPES
            )
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = oauth2_helpers.get_oauth_flow(CONFIG)
                authorization_url, _ = flow.authorization_url(
                    access_type="offline", include_granted_scopes="true"
                )
                return redirect(authorization_url)
        return "Already authorized."

    @app.route("/api/home_automation/oauth2/google/revoke", methods=["POST"])
    def revoke_google_oauth2_token():
        cred = oauth2_helpers.get_google_oauth2_credentials(state_manager)
        params = {"token": cred.token}
        headers = {"content-type": "applications/x-www-form-urlencoded"}
        res = httpx.post(
            "https://oauth2.googleapis.com/revoke", params=params, headers=headers
        )
        return res.text, res.status_code

    @app.route("/api/home_automation/oauth2/google/clear", methods=["DELETE"])
    def clear_google_oauth2_credentials():
        oauth2_helpers.clear_credentials(state_manager)
        return "", 204

    @app.route("/api/home_automation/frontend/build", methods=["POST"])
    def build_frontend():
        start_frontend_build_process()
        return "", 202

    @app.route("/api/home_automation/frontend/deploy", methods=["POST"])
    def deploy_frontend():
        start_frontend_deploy_process()
        return "", 202

    @app.route("/api/home_automation/frontend/reset-image-status", methods=["DELETE"])
    def reset_frontend_image_status():
        state_manager.update_status("building_frontend_image", False)
        state_manager.update_status("pushing_frontend_image", False)
        return "", 204

    return app
