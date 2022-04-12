from home_automation.server.backend import create_app
import home_automation.config

import json
from flask import Response
import pytest

@pytest.fixture
def client():
    app = create_app({"TESTING":True})
    with app.test_client() as client:
        yield client

def assert_response_sucessful(response: Response) -> bool:
    assert json.loads(str(response.data, "utf-8")) == {"success": True}
    assert response.status_code == 200

def test_get_config(client):
    res: Response = client.get("/api/config")
    res_config = home_automation.config.Config(**json.loads(str(res.data, "utf-8")))

    expected = home_automation.config.load_config()
    assert res_config == expected

def test_reload_config(client):
    assert_response_sucessful(client.post("/api/config/reload"))

def test_reorganize_api(client):
    assert_response_sucessful(client.post("/api/reorganize"))

def test_compress_api(client):
    assert_response_sucessful(client.post("/api/compress"))
