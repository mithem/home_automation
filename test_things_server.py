from flask.helpers import url_for
from things_server import create_app, ran_script
import pytest
from flask import Flask


@pytest.fixture
def app():
    return create_app()


class TestMarkHomeworkAsDone:
    def test_mark_homework_as_done_missing_parameter(self, client):
        r = client.post("/api/v1/markhomeworkasdone")
        assert r.status_code == 400
        assert r.data == b"Missing subject parameter"

    def test_mark_homework_as_done_subject_not_found(self, client):
        r = client.post(url_for("mark_homework_as_done", subject="HA"))
        assert r.status_code == 404
        assert r.data == b"Subject not found."

    def test_mark_homework_as_done_successful(self, client):
        r = client.post(url_for("mark_homework_as_done",
                                subject="PH", testing=True))
        assert r.status_code == 200
        assert r.data == ran_script


class TestCreateThingsTaskToUpdateHass():
    """Probably the most useless test I've ever seen."""

    def test_create_things_task_to_update_hass(self, client):
        r = client.post(
            url_for("create_things_task_to_update_hass", testing=True))
        assert r.status_code == 200
        assert r.data == ran_script


def test_not_found(client):
    r = client.get("/")
    assert r.status_code == 404
    assert r.data == b"Not found."
