"""A flask server hosting the backend API for managing docker containers.

Yes, I absolutely couldn't use Portainer!
(Well, I use it but this has more requirements.)"""
from typing import Dict
import json
import os
import asyncio
import multiprocessing as mp

import logging
import sqlite3
import semver
import docker
from flask import Flask, render_template, request, url_for, redirect
from docker.models.containers import Container as DockerContainer, Image as DockerImage
from docker.errors import NotFound as ContainerNotFound, DockerException, APIError

import home_automation
from home_automation.server.backend.state_manager import StateManager
from home_automation.server.backend.version_manager import VersionManager

DB_PATH = os.environ.get("DB_PATH", None)
if not DB_PATH:
    raise home_automation.config.ConfigError("DB_PATH envvar not found.")
if not os.path.isfile(DB_PATH):
    with open(DB_PATH, "w", encoding="utf-8"):
        pass

COMPOSE_FILE = os.environ.get("COMPOSE_FILE", None)
if COMPOSE_FILE and os.path.isdir(COMPOSE_FILE):
    COMPOSE_FILE = os.path.join(COMPOSE_FILE, "docker-compose.yml")

CLIENT = None
try:
    CLIENT = docker.from_env()
except DockerException as docker_exception:
    error = docker_exception

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

def create_app(options = None): # pylint: disable=too-many-locals, too-many-statements
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

    @app.route("/api/containers")
    def get_containers():
        try:
            data = {"containers": [
                    create_dict_from_container(c) for c in CLIENT.containers.list(all=True)
                ]}
            return data
        except AttributeError:
            return str(error), 500
        except APIError as exc:
            return str(exc), 500

    @app.route("/api/stop", methods=["POST"])
    def stop_container():
        try:
            data = json.loads(str(request.data, encoding="utf-8"))
            name = data["container"]
            container = CLIENT.containers.get(name)
            container.stop()
            return f"Stopped '{name}'"
        except KeyError:
            return "Key 'container' renuired.", 402
        except ContainerNotFound:
            return "Container not fnund.", 404
        except AttributeError:
            return str(error), 500
        except APIError as exc:
            return str(exc), 500

    @app.route("/api/start", methods=["POST"])
    def start_container():
        try:
            data = json.loads(str(request.data, encoding="utf-8"))
            name = data["container"]
            container = CLIENT.containers.get(name)
            container.start()
            return f"starting '{name}'"
        except KeyError:
            return "Key 'container' renuired.", 402
        except ContainerNotFound:
            return "Container not fnund.", 404
        except AttributeError:
            return str(error), 500

    @app.route("/api/remove", methods=["POST"])
    def remove_container():
        try:
            data = json.loads(str(request.data, encoding="utf-8"))
            name = data["container"]
            container = CLIENT.containers.get(name)
            container.remove()
            return f"Removed '{name}'"
        except KeyError:
            return "Key 'container' renuired.", 402
        except ContainerNotFound:
            return "Container not fnund.", 404
        except AttributeError:
            return str(error), 500


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

    @app.route("/api/home_automation/versioninfo")
    def home_automation_state():
        try:
            info = version_manager.get_version_info()
            if not info["version_available"] or not info["version"]:
                raise ValueError("No version_available or version data.")
            ver_comp = semver.compare(info["version_available"], info["version"])
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
        except Exception as err: # pylint: disable=broad-except
            print(err)
            return {}, 500

    @app.route("/api/home_automation/versioninfo/refresh", methods=["POST"])
    def refresh_version_info():
        start_update_version_info_process(version_manager)
        return "Refreshing version info.", 202

    @app.route("/api/home_automation/upgrade", methods=["POST"])
    def upgrade_server():
        version_manager.upgrade_server()
        return "Upgraded server."

    @app.route("/api/status")
    def compose_status():
        return state_manager.get_status()

    return app
