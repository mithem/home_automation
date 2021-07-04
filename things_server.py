import os
from flask import Flask, request
import argparse


script_loc_mark_homework_as_done = "/Users/miguel/Library/Mobile Documents/com~apple~Automator/\
Documents/MarkHomeworkAsDone.scpt"
script_loc_create_things_task_to_update_hass = "/Users/miguel/Library/"\
    + "Mobile Documents/com~apple~Automator/Documents/"\
    + "CreateThingsTaskToUpdateHass.scpt"

parser = argparse.ArgumentParser()
parser.add_argument("--port", "-p", type=int, default=8001)
args = parser.parse_args()

app = Flask("auto_react_to_changes_in_homework_server")


@app.route("/api/v1/markhomeworkasdone", methods=["POST"])
def markhomeworkasdone():
    subject = request.args.get("subject", "")
    try:
        s = subject.upper()
        os.system(f"osascript '{script_loc_mark_homework_as_done}' {s}")
        return "Ran script"
    except KeyError:
        return "Missing subject parameter"


@app.route("/api/v1/create-things-task-to-update-hass", methods=["POST"])
def create_things_task_to_update_hass():
    os.system(f"osascript '{script_loc_create_things_task_to_update_hass}'")
    return "Ran script"


if __name__ == "__main__":
    app.run("0.0.0.0", args.port)
