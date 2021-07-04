# just need to implement this by myself as dotenv isn't easily available on
# Synology DSM.
import os

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


def load_dotenv():
    def load(s: str):
        with open(s, "r") as f:
            lines = f.readlines()
        for line in lines:
            varname, value = line.split("=")
            os.environ[varname] = value.replace("\n", "")
    try:
        load(".env")
    except FileNotFoundError:
        load("/volume2/repos/home-automation/.env")
    keys_not_found = []
    for key in _required_keys:
        value = os.environ.get(key)
        if value is None:
            keys_not_found.append(key)
    if len(keys_not_found):
        raise ConfigError(
            "The following variables could not be found in the environment: "
            + ", ".join(keys_not_found))
