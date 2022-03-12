import email
import os

import pytest
from home_automation.config import ConfigEmail, parse_config, Config

TESTING_CONFIG = Config(log_dir="/var/logs", homework_dir="/volume2/Hausaufgaben/HAs", archive_dir="/volume2/Hausaufgaben/Archive", db_path="home_automation.backend.db", compose_file="docker-compose.yml", extra_compress_dirs=[
                        "/mnt/extra1", "/mnt/extra2"], moodle_dl_dir="~/moodle", email={"address": "hello@github.com", "password": "passw0rd1"}, home_assistant={"url": "http://homeassistant.local:8123", "token": "abcABC123!"}, portainer={}, things_server={"url": "http://localhost:8001"})


class TestConfig:
    def test_parse_config_minimum(self):
        config = """
        log_dir: /var/log/home_automation
        homework_dir: /mnt/MassStorage/Hausaufgaben
        archive_dir: /mnt/MassStorage/Hausaufgaben/Archive
        db_path: ./home_automation.backend.db
        compose_file: /mnt/FastStorage/docker-compose.yml
        email:
            address: 'hello@example.com'
            password: "helloworld!"
        """

        expected = Config(
            log_dir="/var/log/home_automation",
            homework_dir="/mnt/MassStorage/Hausaufgaben",
            archive_dir="/mnt/MassStorage/Hausaufgaben/Archive",
            db_path="./home_automation.backend.db",
            compose_file="/mnt/FastStorage/docker-compose.yml",
            email={"address": "hello@example.com", "password": "helloworld!"}
        )

        result = parse_config(config)

        assert result == expected

    def test_parse_config_maximum(self):
        config = """
        log_dir: /var/log/home_automation
        homework_dir: /mnt/MassStorage/Hausaufgaben
        archive_dir: /mnt/MassStorage/Hausaufgaben/Archive
        db_path: ./home_automation.backend.db
        compose_file: /mnt/FastStorage/docker-compose.yml
        extra_compress_dirs:
            - extra1
            - extr2
        moodle_dl_dir: ~/moodle
        email:
            address: 'hello@example.com'
            password: "helloworld!"
        home_assistant:
            url: 'http://homeassistant.local:8123'
            token: 'abcABC123!'
        portainer:
            url: 'http://portainer.local:10201'
        things_server:
            url: 'http://things.local:8001'
        process:
            user: 'user'
            group: 'group'
        runner:
            cron_user: 'user'
        """

        expected = Config(
            log_dir="/var/log/home_automation",
            homework_dir="/mnt/MassStorage/Hausaufgaben",
            archive_dir="/mnt/MassStorage/Hausaufgaben/Archive",
            db_path="./home_automation.backend.db",
            compose_file="/mnt/FastStorage/docker-compose.yml",
            extra_compress_dirs=["extra1", "extr2"],
            moodle_dl_dir="~/moodle",
            email={"address": "hello@example.com", "password": "helloworld!"},
            home_assistant={
                "url": "http://homeassistant.local:8123", "token": "abcABC123!"},
            portainer={"url": "http://portainer.local:10201"},
            things_server={"url": "http://things.local:8001"},
            process={"user": "user", "group": "group"},
            runner={"cron_user": "user"}
        )

        result = parse_config(config)

        assert result == expected
