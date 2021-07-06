# just need to implement this by myself as dotenv isn't easily available on
# Synology DSM.
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
    pass


def parse_config(lines: List[str]) -> Dict[str, str]:
    d = {}
    for line in lines:
        key, value = line.split("=")
        if value.endswith("\n"):
            value = value.replace("\n", "")
        d[key] = value

    keys_not_found = []
    keys = d.keys()
    for key in _required_keys:
        if key not in keys:
            keys_not_found.append(key)

    if len(keys_not_found):
        raise ConfigError(
            "The following variables could not be found in the environment: "
            + ", ".join(keys_not_found))
    return d


def load_into_environment(config: Dict[str, str]):
    for key, value in config.items():
        os.environ[key] = value


def load_dotenv():
    def load(path: str):
        with open(path, "r") as f:
            load_into_environment(parse_config(f.readlines()))
    try:
        load(".env")
    except FileNotFoundError:
        load("/volume2/repos/home-automation/.env")
