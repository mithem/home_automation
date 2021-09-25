import pytest
import home_automation
import docker
import json
from flask import Response

from home_automation.server.backend import create_app

docker_client = docker.from_env()

@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        yield client

def test_get_containers(client):
    cs = docker_client.containers.list()

    res: Response = client.get("/api/containers")
    data = json.loads(str(res.data, "utf-8"))

    assert len(data["containers"]) == len(cs) # just accept future additions