from Home_Automation.config import (
    parse_config,
    load_into_environment,
    ConfigError
)
import pytest
import os

valid_config = [
    "EMAIL_ADDRESS=hello@github.com",
    "EMAIL_PASSWD=passw0rd1",
    "LOG_DIR=/var/logs\n",
    "HASS_TOKEN=abcABC123\n",
    "HASS_BASE_URL=http://homeassistant.local:8123",
    "THINGS_SERVER_URL=http://192.168.2.197:8001\n",
    "ANOTHER=hello"
]


def test_parse_config_valid_config():
    expected = {
        "EMAIL_ADDRESS": "hello@github.com",
        "EMAIL_PASSWD": "passw0rd1",
        "LOG_DIR": "/var/logs",
        "HASS_TOKEN": "abcABC123",
        "HASS_BASE_URL": "http://homeassistant.local:8123",
        "THINGS_SERVER_URL": "http://192.168.2.197:8001",
        "ANOTHER": "hello"
    }

    result = parse_config(valid_config)

    assert result == expected


def test_parse_config_raises_exception_when_config_incomplete():
    config = [
        "EMAIL_ADDRESS=hello@github.com",
        "EMAIL_PASSWD=passw0rd1"
    ]
    with pytest.raises(ConfigError):
        parse_config(config)


def test_load_into_environment():
    # for that, it's fine to use a function tested somewhere else
    config = parse_config(valid_config)
    load_into_environment(config)

    for key, value in config.items():
        assert os.environ[key] == value
