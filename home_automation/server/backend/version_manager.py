"""VersionManager is responsible for comparing the current
to the available version and upgrading if wanted."""
import datetime
import re
import os
import logging
from typing import List, Optional

import git
import requests
import semver

from home_automation import constants
import home_automation.utilities
from home_automation.config import Config
from home_automation.server.backend.state_manager import StateManager

REPO_INIT_FILE_URL = "https://raw.githubusercontent.com/\
mithem/home_automation/master/home_automation/__init__.py"
TESTING_INIT_FILE_URL = "http://localhost:10001/api/testing/version-initfile"
INIT_FILE_URL = REPO_INIT_FILE_URL

testing = os.environ.get("TESTING", False)
if int(testing):
    print("Testing mode active!")
    INIT_FILE_URL = TESTING_INIT_FILE_URL

SQL_TO_PYTHON_KEY_NAME = {
    "versionAvailable": "version_available",
    "versionAvailableSince": "version_available_since",
}


class RemoteNotFoundError(Exception):
    """Remote to pull from not found (configured in home_automation.git.remotes)."""


class BranchNotFoundError(Exception):
    """Branch to pull not found (configured in home_automation.git.branch)."""


class VersionManager:
    """VersionManager is responsible for comparing the current
    to the available version and upgrading if wanted."""

    config: Config

    def __init__(self, config: Config):
        global INIT_FILE_URL  # pylint: disable=global-statement
        self.config = config
        self.state_manager = StateManager(config)
        if testing:
            INIT_FILE_URL = REPO_INIT_FILE_URL
            self.update_version_info()
            INIT_FILE_URL = TESTING_INIT_FILE_URL

    @staticmethod
    def _make_value(key, value: str):
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
        keys = [
            "home_automation-status-" + key
            for key in ["version", "versionAvailable", "versionAvailableSince"]
        ]
        elements = []
        for key in keys:
            elements.append((key, self.state_manager.get_value(key)))
        for elem in elements:
            key = SQL_TO_PYTHON_KEY_NAME.get(elem[0], elem[0])
            value = VersionManager._make_value(key, elem[1])
            data[key] = value
        return data

    def new_version_available(self) -> Optional[str]:
        """Return any new version available. None if no new version is available."""
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
            response = requests.get(
                INIT_FILE_URL, None, timeout=constants.NETWORK_CALLS_TIMEOUT
            )
            text = "\n".join(
                filter(lambda x: x.startswith("VERSION"), response.text.split("\n"))
            )
            match = re.match(
                r"VERSION ?= ?(\"|')(?P<version>\d+\.\d+\.\d+(-?(?P<prerelease>\w+))?)(\"|')",
                text,
            )
        except Exception as exc:  # pylint: disable=broad-except
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
        logging.info("Version available: %s", version_available)

    def upgrade_server(self):
        """Upgrade the server. Restarts it. BLOCKING!"""
        logging.info("Upgrading server...")
        repo = git.Repo(os.curdir)
        if self.config.git.discard_changes:
            logging.info("Discarding changes in repo...")
            repo.git.reset("--hard")
        # please (don't) fail spectaculary
        branch_name = self.config.git.branch
        if branch_name is None:
            branch_name = "master"
        try:
            branch = list(filter(lambda b: b.name == branch_name, repo.branches))[0]
        except IndexError:
            raise BranchNotFoundError(  # pylint: disable=raise-missing-from
                f"Branch {branch_name} not found."
            )
        # seriously, though, that should not happen and isn't this project's responsibility
        remotes: List[str] = []
        if len(self.config.git.remotes) == 0:
            remotes = repo.remotes
        else:
            remotes = filter(lambda r: r.name in self.config.git.remotes, repo.remotes)
        plural = "s" if len(remotes) > 1 else ""
        remotes_str = ", ".join(map(lambda r: r.name, remotes))
        if len(remotes) == 0:
            raise RemoteNotFoundError(f"Remote{plural} not found: {remotes_str}")
        logging.info("Pulling from remote%s: %s", plural, remotes_str)
        for remote in remotes:
            repo.git.pull(remote.name, branch)
        os.system("bash script/restart-runner &")

    def auto_upgrade(self):
        """Check for updated version. If upgrade is available, upgrade. Inform user via mail."""
        self.update_version_info()
        available = self.new_version_available()
        if not available:
            return
        self.inform_user_of_upgrade()
        self.upgrade_server()

    def inform_user_of_upgrade(self):
        """Inform user via mail about upgrading to new version."""
        version_available = self.get_version_info()["version_available"]
        home_automation.utilities.send_mail(
            "Home Automation - VersionManager",
            f"Home Automation will now update to {version_available}",
        )
