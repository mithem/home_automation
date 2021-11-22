"""VersionManager is responsible for comparing the current
to the available version and upgrading if wanted."""
import datetime
import re
import os
import logging
from typing import Optional

import git
import requests
import semver

import home_automation
from home_automation.server.backend.state_manager \
        import StateManager

REPO_INIT_FILE_URL = "https://raw.githubusercontent.com/mithem/home_automation/master/home_automation/__init__.py"
TESTING_INIT_FILE_URL = "http://localhost:10001/api/testing/version-initfile"
INIT_FILE_URL = REPO_INIT_FILE_URL

testing = os.environ.get("TESTING", False)
if int(testing):
    print("Testing mode active!")
    INIT_FILE_URL = TESTING_INIT_FILE_URL

SQL_TO_PYTHON_KEY_NAME = {
        "versionAvailable": "version_available",
        "versionAvailableSince": "version_available_since"
}

class VersionManager: # pylint: disable=no-self-use
    """VersionManager is responsible for comparing the current
    to the available version and upgrading if wanted."""
    def __init__(self, db_path: str):
        global INIT_FILE_URL
        self.state_manager = StateManager(db_path)
        if testing:
            INIT_FILE_URL = REPO_INIT_FILE_URL
            self.update_version_info()
            INIT_FILE_URL = TESTING_INIT_FILE_URL

    def _make_value(self, key, value: str):
        if value == "":
            return None
        try:
            if key == "version_available":
                return value
            if key == "version_available_since":
                return datetime.datetime.fromisoformat(value)
            return value
        except ValueError:
            return value

    def get_version_info(self):
        """Return version information in the following format:

        {
            "version": str,
            "version_available": str,
            "version_available_since": datetime.datetime
        }"""
        data = {}
        elements = self.state_manager.execute("SELECT * FROM status WH\
ERE key='version' OR key='versionAvailable' OR key='versionAvailableSince'")
        for elem in elements:
            key = SQL_TO_PYTHON_KEY_NAME.get(elem[0], elem[0])
            value = self._make_value(key, elem[1])
            data[key] = value
        return data

    def new_version_available(self) -> Optional[str]:
        info = self.get_version_info()
        if not info["version_available"] or not info["version"]:
            raise ValueError("No version_available or version data.")
        ver_comp = semver.compare(info["version_available"], info["version"])
        if ver_comp > 0:
            return info["version_available"]
        return None


    def update_version_info(self):
        """Refresh the version information. BLOCKING!"""
        def fallback():
            self.state_manager.update_status("version", home_automation.VERSION)
            self.state_manager.update_status("versionAvailable", "")
            self.state_manager.update_status("versionAvailableSince", "")

        logging.info("Updating version info...")
        try:
            response = requests.get(INIT_FILE_URL, None)
            text = "\n".join(filter(lambda x: x.startswith("VERSION"), response.text.split("\n")))
            match = re.match(r"VERSION ?= ?(\"|')(?P<version>\d+\.\d+\.\d+(-?(?P<prerelease>\w+))?)(\"|')", text)
        except Exception as exc: # pylint: disable=broad-except
            logging.error(exc)
            fallback()
            return
        if not match:
            fallback()
            return
        groupd = match.groupdict()
        if groupd.get("version", None) is None:
            fallback()
            return
        version_available = groupd.get("version")
        available_since = datetime.datetime.now().isoformat()
        self.state_manager.update_status("version", home_automation.VERSION)
        self.state_manager.update_status("versionAvailable", version_available)
        self.state_manager.update_status("versionAvailableSince", available_since)
        logging.info(f"Version available: {version_available}")

    def upgrade_server(self):
        """Upgrade the server. Restarts it. BLOCKING!"""
        logging.info("Upgrading server...")
        repo = git.Repo(os.curdir)
        # please (don't) fail spectaculary
        branch = list(filter(lambda b: b.name == "master", repo.branches))[0]
        # seriously, though, that should not happen and isn't this project's responsibility
        for remote in repo.remotes:
            repo.git.pull(remote.name, branch)
        os.system("script/restart-runner &")

    def auto_upgrade(self):
        """Check for updated version. If upgrade is available, upgrade. Inform user via mail."""
        self.update_version_info()
        available = self.new_version_available()
        if not available:
            return
        self.upgrade_server()
        self.inform_user_of_upgrade()

    def inform_user_of_upgrade(self):
        current_version = self.get_version_info()["version"]
        home_automation.send_mail("Home Automation - VersionManager", f"Home Automation was just updated to {current_version}")
