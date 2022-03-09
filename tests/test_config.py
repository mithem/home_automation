import email
import os

import pytest
from home_automation.config import ConfigEmail, parse_config, Config


class TestConfig:
    def test_parse_config(self):
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
            compose_file="/mnt/FastStorage/docker-compose.y ml",
            email={"address": "hello@example.com", "password": "helloWorld!"}
        )

        print(expected.email)

        result = parse_config(config)

        print(result.email)

        assert result == expected
