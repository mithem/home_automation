import os
from flask import Flask, request
import argparse
from flask.templating import render_template
from flask.wrappers import Response
from ArchiveManager import abbr_to_subject


script_loc_mark_homework_as_done = "/Users/miguel/Library/Mobile Documents/com~apple~Automator/\
Documents/MarkHomeworkAsDone.scpt"
script_loc_create_things_task_to_update_hass = "/Users/miguel/Library/"\
    + "Mobile Documents/com~apple~Automator/Documents/"\
    + "CreateThingsTaskToUpdateHass.scpt"

valid_subject_abbr = [s.upper() for s in abbr_to_subject.keys()]
ran_script = b"Ran script."

def create_app() -> Flask:
    app = Flask(__name__)

    @app.errorhandler(404)
    def not_found(error):
        return "Not found.", 404

    @app.route("/api/v1/markhomeworkasdone", methods=["POST"])
    def mark_homework_as_done():
        subject = request.args.get("subject", None)
        testing = request.args.get("testing", False)
        if subject is None:
            return Response("Missing subject parameter", 400)

        s = subject.upper()
        if s not in valid_subject_abbr:
            return "Subject not found.", 404
        
        if testing:
            return ran_script

        os.system(f"osascript '{script_loc_mark_homework_as_done}' {s}")
        return ran_script


    @app.route("/api/v1/create-things-task-to-update-hass", methods=["POST"])
    def create_things_task_to_update_hass():
        testing = request.args.get("testing", False)
        if testing:
            return ran_script
        os.system(f"osascript '{script_loc_create_things_task_to_update_hass}'")
        return ran_script

    return app
