"""A server intended to create tasks in Things when appropriate."""
import os

from flask import Flask, request
from flask.wrappers import Response
from home_automation.archive_manager import ABBR_TO_SUBJECT

SCRIPT_LOC_MARK_HOMEWORK_AS_DONE = "/Users/miguel/Library/Mobile Documents/com~apple~Automator/\
Documents/MarkHomeworkAsDone.scpt"
SCRIPT_LOC_CREATE_TASK_IN_THINGS_TO_UPDATE_HASS = "/Users/miguel/Library/"\
    + "Mobile Documents/com~apple~Automator/Documents/"\
    + "CreateThingsTaskToUpdateHass.scpt"

VALID_SUBJECT_ABBRS = [s.upper() for s in ABBR_TO_SUBJECT.keys()] # pylint: disable=consider-iterating-dictionary
RAN_SCRIPT = b"Ran script."


def create_app() -> Flask:
    """App factory."""
    app = Flask(__name__)

    @app.errorhandler(404)
    def not_found(error): # pylint: disable=unused-argument
        """404 error handler."""
        return "Not found.", 404

    @app.route("/api/v1/markhomeworkasdone", methods=["POST"])
    def mark_homework_as_done():
        """Mark the corresponding homework (identified via query) as done in Things."""
        subject = request.args.get("subject", None)
        testing = request.args.get("testing", False)
        if subject is None:
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

    return app
