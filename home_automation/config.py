"""A workaround for dotenv not being available on Synology DSM."""
import os
import re
from turtle import st
import yaml
from typing import Any, List, Dict, Optional

from logging import Logger


class ConfigEmail:
    """Email configuration."""
    address: str
    password: str

    def __new__(self, address: str, password: str):
        self.address = address
        self.password = password
        return self

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.address == other.address and
            self.password == other.password
        )


class ConfigHomeAssistant:
    """Home Assistant configuration."""
    token: str
    base_url: str
    insecure_https: bool

    def __new__(self, data: Dict[str, str]):
        token = data.get("token")
        base_url = data.get("base_url")
        insecure_https = data.get("insecure_https", False)

        if not token or not base_url:
            return None

        self.token = token
        self.base_url = base_url
        self.insecure_https = insecure_https
        return self

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.token == other.token and
            self.base_url == other.base_url and
            self.insecure_https == other.insecure_https
        )


class ConfigPortainer:
    """Portainer configuration."""
    url: str
    username: str
    password: str
    insecure_https: bool

    def __new__(self, data: Dict[str, str]):
        url = data.get("url")
        username = data.get("username")
        password = data.get("password")
        insecure_https = data.get("insecure_https", False)

        if not url or not username or not password:
            return None

        self.url = url
        self.username = username
        self.password = password
        self.insecure_https = insecure_https
        return self

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.url == other.url and
            self.username == other.username and
            self.password == other.password and
            self.insecure_https == other.insecure_https
        )


class ConfigThingsServer:
    """Things server configuration."""
    url: str
    insecure_https: bool

    def __new__(self, data: Dict[str, str]):
        url = data.get("url")
        insecure_https = data.get("insecure_https", False)

        if not url:
            return None

        self.url = url
        self.insecure_https = insecure_https
        return self

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.url == other.url and
            self.insecure_https == other.insecure_https
        )


class ConfigProcess:
    """Configuration of the home_automation process."""
    user: Optional[str]
    group: Optional[str]

    def __new__(self, data: Dict[str, str]):
        self.user = data.get("user")
        self.group = data.get("group")

        if not self.user and not self.group:
            return None

        return self

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.user == other.user and
            self.group == other.group
        )


class ConfigRunner:
    cron_user: Optional[str]

    def __new__(self, data: Dict[str, str]):
        cron_user = data.get("cron_user")
        if not cron_user:
            return None
        self.cron_user = cron_user



class Config:
    """Configuration data."""
    log_dir: str
    homework_dir: str
    archive_dir: str
    db_path: str
    compose_file: str
    extra_compress_dirs: List[str]
    moodle_dl_dir: Optional[str]
    email: ConfigEmail
    home_assistant: Optional[ConfigHomeAssistant]
    portainer: Optional[ConfigPortainer]
    things_server: Optional[ConfigThingsServer]
    process: Optional[ConfigProcess]
    runner: Optional[ConfigRunner]

    def __init__(self, log_dir: str,
                 homework_dir: str,
                 archive_dir: str,
                 db_path: str,
                 compose_file: str,
                 email: Dict[str, str],
                 home_assistant: Dict[str, Any] = dict(),
                 portainer: Dict[str, Any] = dict(),
                 things_server: Dict[str, Any] = dict(),
                 process: Dict[str, str] = dict(),
                 runner: Dict[str, str] = dict(),
                 extra_compress_dirs: List[str] = [],
                 moodle_dl_dir: Optional[str] = None
                 ):
        self.log_dir = log_dir
        self.homework_dir = homework_dir
        self.archive_dir = archive_dir
        self.db_path = db_path
        self.compose_file = compose_file
        self.moodle_dl_dir = moodle_dl_dir
        self.extra_compress_dirs = extra_compress_dirs
        self.email = ConfigEmail(**email)
        self.home_assistant = ConfigHomeAssistant(home_assistant)
        self.portainer = ConfigPortainer(portainer)
        self.things_server = ConfigThingsServer(things_server)
        self.process = ConfigProcess(process)
        self.runner = ConfigRunner(config_runner)

    def __str__(self) -> str:
        return str(vars(self))

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other) -> bool:
        return (
            self.log_dir == other.log_dir and
            self.homework_dir == other.homework_dir and
            self.archive_dir == other.archive_dir and
            self.db_path == other.db_path and
            self.compose_file == other.compose_file and
            self.moodle_dl_dir == other.moodle_dl_dir and
            self.email == other.email and
            self.home_assistant == other.home_assistant and
            self.portainer == other.portainer and
            self.things_server == other.things_server and
            self.process == other.process
        )


class ConfigError(Exception):
    """An exception thrown when the config is oncomplete or invalid."""


def load_config(logger: Logger = None, path: str = "home_automation.conf.yml") -> Config:
    """Load config from file and return it."""
    with open(path, "r", encoding="utf-8") as file_obj:
        return parse_config(file_obj.read())


def parse_config(config: str) -> Config:
    config = yaml.safe_load(config)
    return Config(**config)
