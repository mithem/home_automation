from unittest import TestCase
from home_automation.server.backend import create_app
import home_automation.config

import os
import json
from flask import Response
import pytest


def assert_response_sucessful(response: Response) -> bool:
    assert json.loads(str(response.data, "utf-8")) == {"success": True}
    assert response.status_code == 200


@pytest.fixture
def client():
    # would have used a class and out the following 5 lines in its setUp method, but pytest fixtures seem to be incompatible with unittest.TestCase.setUp()
    config = home_automation.config.load_config()
    dirs = [config.archive_dir, config.homework_dir]
    for path in dirs:
        if not os.path.exists(path):
            os.makedirs(path)
    app = create_app({"TESTING": True})
    with app.test_client() as test_client:
        yield test_client


def test_get_config(client):
    res: Response = client.get("/api/config")
    res_config = home_automation.config.Config(
        **json.loads(str(res.data, "utf-8")))

    expected = home_automation.config.load_config()
    print(res_config)
    print(expected)
    assert res_config == expected


def test_reload_config(client):
    assert_response_sucessful(client.post("/api/config/reload"))


def test_reorganize_api(client):
    assert_response_sucessful(client.post("/api/reorganize"))


def test_compress_api(client):
    assert_response_sucessful(client.post("/api/compress"))
