#!python3
# pylint: disable=invalid-name
"""Run moodle-dl."""
import moodle_dl.main
import home_automation.config

config = home_automation.config.load_config()

moodle_dl.main.main(["--path", config.moodle_dl_dir])
