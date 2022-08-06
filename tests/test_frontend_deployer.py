from typing import Tuple

import pytest
from home_automation import VERSION
from home_automation import frontend_deployer as fd
from home_automation.config import Config


class ParseRegistryURLTestRun:
    input: str
    output: Tuple[str, str]

    def __init__(self, input, output):
        self.input = input
        self.output = output

    def run(self):
        config = Config(
            log_dir="",
            homework_dir="",
            archive_dir="",
            db_path="",
            compose_file="",
            email={},
            docker={"registry": {"registry_url": self.input}},
        )
        assert fd._parse_registry_url(config) == (self.output[0], self.output[1])


class GetImageTagTestRun:
    input: str
    output: str

    def __init__(self, input, output):
        self.input = input
        self.output = output

    def run(self):
        config = Config(
            log_dir="",
            homework_dir="",
            archive_dir="",
            db_path="",
            compose_file="",
            email={},
            frontend={"image_name": self.input},
        )
        assert fd._get_image_tag(config) == self.output


def test_parse_registry_url_root_domain():
    run = ParseRegistryURLTestRun(
        input="https://registry.com",
        output=("registry.com", "registry-com"),
    )
    run.run()


def test_parse_registry_url_multiple_subdomains():
    run = ParseRegistryURLTestRun(
        input="https://registry.hub.docker.com",
        output=("registry.hub.docker.com", "registry-hub-docker-com"),
    )
    run.run()


def test_parse_registry_url_http():
    run = ParseRegistryURLTestRun(
        input="http://registry.example.com",
        output=("registry.example.com", "registry-example-com"),
    )
    run.run()


def test_parse_registry_url_accepts_port():
    run = ParseRegistryURLTestRun(
        input="https://registry.example.com:5000",
        output=("registry.example.com", "registry-example-com"),
    )
    run.run()


def test_parse_registry_url_accepts_valid_domains():
    run = ParseRegistryURLTestRun(
        input="https://hello_world.home-lab.k8s.local",
        output=("hello_world.home-lab.k8s.local", "hello_world-home-lab-k8s-local"),
    )
    run.run()


def test_parse_registry_url_raises_value_error_no_scheme():
    run = ParseRegistryURLTestRun(
        input="registry.example.com",
        output=("registry.example.com", "registry-example-com"),
    )
    with pytest.raises(
        ValueError,
        match=r"Invalid registry URL 'registry\.example\.com'\. Could not extract host from it\.",
    ):
        run.run()


def test_parse_registry_url_raises_value_error_invalid_scheme():
    run = ParseRegistryURLTestRun(
        input="ntp://registry.example.com",
        output=("registry.example.com", "registry-example-com"),
    )
    with pytest.raises(
        ValueError,
        match=r"Invalid registry URL 'ntp://registry\.example\.com'\. Could not extract host from it\.",
    ):
        run.run()


def test_parse_registry_url_raises_value_error_special_chars():
    run = ParseRegistryURLTestRun(
        input="https://hello+w0rl$.example.ß",
        output=("hello+w0rl$.example.ß", "hello+w0rl$-example-ß"),
    )
    with pytest.raises(
        ValueError,
        match=r"Invalid registry URL 'https://hello\+w0rl\$\.example\.ß'\. Could not extract host from it\.",
    ):
        run.run()


def test_parse_registry_url_raises_value_error_path_given():
    run = ParseRegistryURLTestRun(
        input="https://registry.example.com/path",
        output=("registry.example.com", "registry-example-com"),
    )
    with pytest.raises(
        ValueError,
        match=r"Invalid registry URL 'https://registry\.example\.com/path'\. Could not extract host from it\.",
    ):
        run.run()


def test_get_image_tag():
    run = GetImageTagTestRun(
        input="hello_world",
        output=f"hello_world:{VERSION}",
    )
    run.run()


def test_get_image_tag_image_from_registry():
    run = GetImageTagTestRun(
        input="registry.example.com/hello_world",
        output=f"registry.example.com/hello_world:{VERSION}",
    )
    run.run()


def test_get_image_tag_image_from_registry_with_custom_port():
    run = GetImageTagTestRun(
        input="registry.example.com:5000/hello_world",
        output=f"registry.example.com:5000/hello_world:{VERSION}",
    )
    run.run()


def test_get_image_tag_raises_value_error_frontend_image_name_already_tagged():
    # Shall raise ValueError when frontend.image_name already contains a tag like home-automation-frontend:2.0.0
    run = GetImageTagTestRun(
        input="hello_world:2.0.0",
        output="hello_world:2.0.0",
    )
    with pytest.raises(
        ValueError,
        match=r"Invalid frontend image name 'hello_world:2.0.0'\. Image name already contains a tag\.",
    ):
        run.run()


def test_get_image_tag_raises_value_error_invalid_image_name():
    run = GetImageTagTestRun(
        input="hell0_wOrld",
        output="hell0_wOrld",
    )
    with pytest.raises(
        ValueError,
        match=r"Invalid frontend image name 'hell0_wOrld'\.",
    ):
        run.run()
