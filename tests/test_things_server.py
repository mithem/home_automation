import pytest
import pytest_asyncio
from flask.helpers import url_for
from home_automation.things_server import RAN_SCRIPT, create_app


@pytest_asyncio.fixture
def app():
    return create_app()


class TestMarkHomeworkAsDone:
    def test_mark_homework_as_done_missing_parameter(self, client):
        url = url_for("mark_homework_as_done")
        r = client.post(url)
        assert r.status_code == 400
        assert r.data == b"Missing subject parameter"

    def test_mark_homework_as_done_subject_not_found(self, client):
        url = url_for("mark_homework_as_done", subject="HA")
        r = client.post(url)
        assert r.status_code == 404
        assert r.data == b"Subject not found."

    def test_mark_homework_as_done_successful(self, client):
        r = client.post(url_for("mark_homework_as_done",
                                subject="PH", testing=True))
        assert r.status_code == 200
        assert r.data == RAN_SCRIPT


class TestCreateThingsTaskToUpdateHass():
    """Probably the most useless test I've ever seen."""

    def test_create_things_task_to_update_hass(self, client):
        r = client.post(
            url_for("create_things_task_to_update_hass", testing=True))
        assert r.status_code == 200
        assert r.data == RAN_SCRIPT


def test_hello_world(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.data == b"Hello, world!"
