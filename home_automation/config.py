"""A workaround for dotenv not being available on Synology DSM."""
import os
from typing import List, Dict

_required_keys = [
    "EMAIL_ADDRESS",
    "EMAIL_PASSWD",
    "HASS_TOKEN",
    "HASS_BASE_URL",
    "THINGS_SERVER_URL",
    "LOG_DIR"
]


class ConfigError(Exception):
    """An exception thrown when the config is oncomplete or invalid."""


def parse_config(lines: List[str]) -> Dict[str, str]:
    """Parse config and return parsed dict."""
    config = {}
    for line in lines:
        key, value = line.split("=")
        if value.endswith("\n"):
            value = value.replace("\n", "")
        config[key] = value

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
        with open(path, "r") as file:
            load_into_environment(parse_config(file.readlines()))
    try:
        load(".env")
    except FileNotFoundError:
        try:
            load("../.env")
        except FileNotFoundError:
            load("/volume2/repos/home-automation/.env")
