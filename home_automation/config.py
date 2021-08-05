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


def get_config_error(keys_not_found):
    """Prepare and return a ConfigError with the appropriate error message."""
    return ConfigError(
        "The following variables could not be found in the environment: "
        + ", ".join(keys_not_found))


def parse_config(lines: List[str]) -> Dict[str, str]:
    """Parse config and return parsed dict."""
    env_keys = os.environ.keys()
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
        if key not in keys and key not in env_keys:
            keys_not_found.append(key)

    if keys_not_found:
        raise get_config_error(keys_not_found)
    return config


def load_into_environment(config: Dict[str, str], config_to_parse_from_file: List[str] = None):
    """Load the dict into the environment."""
    if config_to_parse_from_file:
        for key in config_to_parse_from_file:
            os.environ[key] = config[key]
    else:
        for key, value in config.items():
            os.environ[key] = value


def load_dotenv():
    """Check if environment contains required values, otherwise
    find the appropriate file and load it's content into the environment."""

    def load(path: str, config_to_parse_from_file: List[str]):
        with open(path, "r") as file_obj:
            load_into_environment(parse_config(
                file_obj.readlines()), config_to_parse_from_file)

    def check() -> List[str]:
        config_to_parse_from_file = []
        for key in _required_keys:
            value = os.environ.get(key, None)
            if not value:
                config_to_parse_from_file.append(key)
        return config_to_parse_from_file

    config_to_parse_from_file = check()
    if config_to_parse_from_file == []:
        return  # no need to search for .env

    try_to_load = [
        ".env",
        "../.env",
        "/mnt/FastStorage/mithem-applications/home_automation/.env",
        "/home_automation/env"
    ]
    loaded = False
    for path in try_to_load:
        try:
            load(path, config_to_parse_from_file)
            loaded = True
            break
        except FileNotFoundError:
            continue

    if not loaded:
        raise ConfigError("Could not find .env file.") from get_config_error(
            [])  # no file -> no lines -> envvars insufficient
