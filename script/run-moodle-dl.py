#!python3
import os

import moodle_dl.main
import home_automation.config

config = home_automation.config.load_config()

moodle_dl.main.main(["--path", config.moodle_dl_dir])
