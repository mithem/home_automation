#!python3
import os

import moodle_dl.main
import home_automation.config

home_automation.config.load_dotenv()

moodle_dl.main.main(["--path", os.environ["MOODLE_DL_DIR"]])
