#!python3
# pylint: disable=invalid-name
"""Run moodle-dl."""
import moodle_dl.main
from home_automation import config as haconfig

config = haconfig.load_config()

moodle_dl.main.main(["--path", config.moodle_dl_dir])
