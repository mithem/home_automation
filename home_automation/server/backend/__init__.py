"""A flask server hosting the backend API for managing docker containers.

Yes, I absolutely couldn't use Portainer!"""
from typing import Dict
import json
import os
import asyncio
import docker

from flask import Flask, render_template, request, url_for, redirect
from docker.models.containers import Container as DockerContainer, Image as DockerImage
from docker.errors import NotFound as ContainerNotFound, DockerException, APIError

COMPOSE_FILE = os.environ.get("COMPOSE_FILE", None)
if COMPOSE_FILE and os.path.isdir(COMPOSE_FILE):
    COMPOSE_FILE = os.path.join(COMPOSE_FILE, "docker-compose.yml")

CLIENT = None
try:
    CLIENT = docker.from_env()
except DockerException as docker_exception:
    error = docker_exception

class STATUS: # pylint: disable=too-few-public-methods
    """Some state-keeping of the status. As a database would be plain overkill."""
    pruning = False
    class COMPOSE:
        """Docker-compose-related state."""
        pulling = False
        upping = False
        downing = False

def create_app(options = None): # pylint: disable=too-many-locals, too-many-statements
    """App factory."""
    app = Flask(__name__)
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

    async def compose_pull_exec():
        os.system(f"docker-compose -f '{COMPOSE_FILE}' pull")
        STATUS.COMPOSE.pulling = False

    async def compose_up_exec():
        os.system(f"docker-compose -f '{COMPOSE_FILE}' up -d")
        STATUS.COMPOSE.upping = False

    async def compose_down_exec():
        os.system(f"docker-compose -f '{COMPOSE_FILE}' down")
        STATUS.COMPOSE.downing = False

    async def docker_prune_exec():
        os.system("docker system prune -af")
        STATUS.pruning = False

    @app.route("/api/compose/pull", methods=["POST"])
    def compose_pull():
        STATUS.COMPOSE.pulling = True
        asyncio.run(compose_pull_exec())
        return "Pulling images."

    @app.route("/api/compose/up", methods=["POST"])
    def compose_up():
        STATUS.COMPOSE.upping = True
        asyncio.run(compose_up_exec())
        return "Upping images."

    @app.route("/api/compose/down", methods=["POST"])
    def compose_down():
        STATUS.COMPOSE.downing = True
        asyncio.run(compose_down_exec())
        return "Downing images."

    @app.route("/api/prune", methods=["DELETE"])
    def docker_prune():
        STATUS.pruning = True
        asyncio.run(docker_prune_exec())
        return "Pruning images."

    @app.route("/api/status")
    def compose_status():
        return {
            "pulling": STATUS.COMPOSE.pulling,
            "upping": STATUS.COMPOSE.upping,
            "downing": STATUS.COMPOSE.downing,
            "pruning": STATUS.pruning
        }
    return app
