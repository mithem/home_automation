"""A server intended to interact with Things when appropriate."""
import os

from flask import Flask, request
from flask.wrappers import Response
from home_automation.constants import ABBR_TO_SUBJECT

SCRIPT_LOC_MARK_HOMEWORK_AS_DONE = \
    "/Users/miguel/repos/home_automation/script/MarkHomeworkAsDone.scpt"
SCRIPT_LOC_CREATE_TASK_IN_THINGS_TO_UPDATE_HASS = \
    "/Users/miguel/repos/home_automation/script/CreateThingsTaskToUpdateHass.scpt"

# pylint: disable=consider-iterating-dictionary
VALID_SUBJECT_ABBRS = [s.upper() for s in ABBR_TO_SUBJECT.keys()]
RAN_SCRIPT = b"Ran script."


def create_app() -> Flask:
    """App factory."""
    app = Flask(__name__)

    @app.errorhandler(404)
    def not_found(error):  # pylint: disable=unused-argument
        """404 error handler."""
        return "Not found.", 404

    @app.route("/api/v1/markhomeworkasdone", methods=["POST"])
    def mark_homework_as_done():
        """Mark the corresponding homework (identified via query) as done in Things."""
        subject = request.args.get("subject", None)
        testing = request.args.get("testing", False)
        if not subject:
            return Response("Missing subject parameter", 400)

        subject = subject.upper()
        if subject not in VALID_SUBJECT_ABBRS:
            return "Subject not found.", 404

        if testing:
            return RAN_SCRIPT

        os.system(f"osascript '{SCRIPT_LOC_MARK_HOMEWORK_AS_DONE}' {subject}")
        return RAN_SCRIPT

    @app.route("/api/v1/create-things-task-to-update-hass", methods=["POST"])
    def create_things_task_to_update_hass():
        """In Things, create a new task: to update hass."""
        testing = request.args.get("testing", False)
        if testing:
            return RAN_SCRIPT

        os.system(
            f"osascript '{SCRIPT_LOC_CREATE_TASK_IN_THINGS_TO_UPDATE_HASS}'")
        return RAN_SCRIPT

    @app.route("/")
    def inde():
        """Index (return hello world)"""
        return "Hello, world!"

    return app
