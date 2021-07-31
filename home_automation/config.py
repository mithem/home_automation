"""A workaround for dotenv not being available on Synology DSM."""
import os
import re
from typing import List, Dict

_required_keys = [
    "EMAIL_ADDRESS",
    "EMAIL_PASSWD",
    "HASS_TOKEN",
    "HASS_BASE_URL",
    "THINGS_SERVER_URL",
    "LOG_DIR",
    "HOMEWORK_DIR",
    "ARCHIVE_DIR"
]


class ConfigError(Exception):
    """An exception thrown when the config is oncomplete or invalid."""


def parse_config(lines: List[str]) -> Dict[str, str]:
    """Parse config and return parsed dict."""
    config = {}
    for line in lines:
        match = re.match(r"(?P<key>[\w_]+)\s?=\s?(?P<value>.*)\n?", line)
        if match:
            groupdict = match.groupdict()
            key = groupdict.get("key")
            value = groupdict.get("value")
            if key and value:
                config[str(key)] = str(value)

    keys_not_found = []
    keys = config.keys()
    for key in _required_keys:
        if key not in keys:
            keys_not_found.append(key)

    if keys_not_found:
        raise ConfigError(
            "The following variables could not be found in the environment: "
            + ", ".join(keys_not_found))
    return config


def load_into_environment(config: Dict[str, str]):
    """Load the dict into the environment."""
    for key, value in config.items():
        os.environ[key] = value


def load_dotenv():
    """Find the appropriate file and load it's content into the environment."""
    def load(path: str):
        with open(path, "r") as file_obj:
            load_into_environment(parse_config(file_obj.readlines()))
    try:
        load(".env")
    except FileNotFoundError:
        try:
            load("../.env")
        except FileNotFoundError:
            load("/mnt/FastStorage/mithem-applications/home_automation/.env")
