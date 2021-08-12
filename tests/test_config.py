import os

import pytest
from home_automation.config import (ConfigError, load_into_environment,
                                    parse_config, load_dotenv, _required_keys)

VALID_CONFIG_LINES = [
    "EMAIL_ADDRESS=hello@github.com",
    "EMAIL_PASSWD=passw0rd1",
    "LOG_DIR=/var/logs\n",
    "HASS_TOKEN=abcABC123\n",
    "HASS_BASE_URL=http://homeassistant.local:8123",
    "THINGS_SERVER_URL=http://192.168.2.197:8001\n",
    "HOMEWORK_DIR = /volume2/Hausaufgaben/HAs",
    "ARCHIVE_DIR = /volume2/Hausaufgaben/Archive",
    "ANOTHER=hello"
]

VALID_CONFIG_DICT = {
    "EMAIL_ADDRESS": "hello@github.com",
    "EMAIL_PASSWD": "passw0rd1",
    "LOG_DIR": "/var/logs",
    "HASS_TOKEN": "abcABC123",
    "HASS_BASE_URL": "http://homeassistant.local:8123",
    "THINGS_SERVER_URL": "http://192.168.2.197:8001",
    "HOMEWORK_DIR": "/volume2/Hausaufgaben/HAs",
    "ARCHIVE_DIR": "/volume2/Hausaufgaben/Archive",
    "ANOTHER": "hello"
}

@pytest.mark.usefixtures("delete_environment_vars")
class EnvironmentSensibleTestCase():
    @pytest.fixture
    def delete_environment_vars(self):
        for key in _required_keys:
            try:
                del os.environ[key]
            except KeyError:
                continue

def test_parse_config_valid_config():

    result = parse_config(VALID_CONFIG_LINES)

    assert result == VALID_CONFIG_DICT


def test_parse_config_raises_exception_when_config_incomplete():
    config = [
        "EMAIL_ADDRESS=hello@github.com",
        "EMAIL_PASSWD=passw0rd1"
    ]
    try:
        # make sure envvars don't allow incomplete config
        del os.environ["ARCHIVE_DIR"]
    except KeyError:
        pass
    with pytest.raises(ConfigError) as excinfo:
        parse_config(config)
    assert "ARCHIVE_DIR" in str(excinfo.value)


class LoadIntoEnvironmentTests(EnvironmentSensibleTestCase):
    def test_load_into_environment_entire_config(self):
        # for that, it's fine to use a function tested somewhere else
        load_into_environment(VALID_CONFIG_DICT)

        for key, value in VALID_CONFIG_DICT.items():
            assert os.environ[key] == value


    def test_load_into_environment_only_specified_keys(self):
        keys_to_load = ["LOG_DIR", "HOMEWORK_DIR"]

        load_into_environment(VALID_CONFIG_DICT, keys_to_load)

        for key, value in VALID_CONFIG_DICT.items():
            if key in keys_to_load:
                assert os.environ[key] == value
            else:
                with pytest.raises(KeyError):
                    # don't need to assert, just can't thing of anything else to do with the value
                    assert not os.environ[key]


    def test_load_dotenv_doesnt_override_env_values(self):
        mail = "test@example.com"
        os.environ["EMAIL_ADDRESS"] = mail
        lines_to_restore = None

        try:
            with open(".env", "r") as f:
                lines_to_restore = f.readlines()
        except FileNotFoundError:
            pass

        with open(".env", "w") as f:
            f.flush()
            f.writelines(VALID_CONFIG_LINES)

        for key, value in VALID_CONFIG_DICT.items():
            if key != "EMAIL_ADDRESS":
                assert os.environ[key] == value
            else:
                assert os.environ["EMAIL_ADDRESS"] == mail

        if lines_to_restore:
            with open(".env", "w") as f:
                f.flush()
                f.writelines(lines_to_restore)
        else:
            os.remove(".env")
