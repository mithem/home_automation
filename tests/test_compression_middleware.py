import os
import sys

import httpx
import pytest
from fileloghelper import Logger

import tests.test_compression_manager
# pytest needs this to be imported in this module
from tests.test_compression_manager import configure_mock_responses  # pylint: disable=unused-import

from tests.test_config import VALID_CONFIG_DICT
from home_automation.compression_middleware import (
    ChangeStatusInThingsMiddleware,
    CompressionMiddleware,
    FlashLightsInHomeAssistantMiddleware,
    InvalidResponseError,
    InvalidFilenameError,
    SubjectCompressionMiddleware
)
from home_automation import config

# because of dynamic constant creation
# pylint: disable=undefined-variable


_logger = Logger()
config.load_into_environment(VALID_CONFIG_DICT)
keys_to_set_as__module_constants = [
    "HASS_BASE_URL",
    "HASS_TOKEN",
    "THINGS_SERVER_URL",
    "HOMEWORK_DIR"
]

for key in keys_to_set_as__module_constants:
    # https://stackoverflow.com/questions/2933470/how-do-i-call-setattr-on-the-current-module
    value = os.environ[key]
    if value is None:
        raise config.ConfigError(f"{key} not found in env.")
    setattr(sys.modules[__name__], key, value)


@pytest.fixture
def logger():
    return _logger


@pytest.mark.usefixtures("setup_middleware")
class TestCompressionMiddleware:
    @pytest.fixture
    def setup_middleware(self, logger):
        self.middleware = CompressionMiddleware(logger)

    @pytest.mark.asyncio
    async def test_act_raises_not_implemented_error(self, logger):
        with pytest.raises(NotImplementedError):
            await self.middleware.act("")

    def test_handle_response_valid_response(self):
        r = httpx.Response(200)
        assert self.middleware.handle_response(r) is None

    def test_handle_response_invalid_response(self):
        r = httpx.Response(404, text="Not found.")
        with pytest.raises(InvalidResponseError):
            self.middleware.handle_response(r)


@pytest.mark.asyncio
class TestSubjectCompressionMiddleware:

    @pytest.fixture
    def setup_middleware_checking_being_invoked(self, logger):

        class MiddlewareCheckingBeingInvoked(SubjectCompressionMiddleware):
            def __init__(self, logger):
                super().__init__(logger)
                self.executed = False

            async def act_subject_valid(self, filename):
                self.executed = True

        self.middleware = MiddlewareCheckingBeingInvoked(logger)

    @pytest.fixture
    def setup_subject_compression_middleware(self, logger):
        self.middleware = SubjectCompressionMiddleware(logger)

    @pytest.mark.usefixtures("setup_middleware_checking_being_invoked")
    async def test_act_only_acts_on_valid_filenames(self):
        filenames = [
            "PH HA 22-06-2021.pdf",
            "PH experiment results.py",
            "PH KW 25.pdf",
            "PH Klausurvorbereitung 4. Klausur.pdf"
        ]

        for f in filenames:
            await self.middleware.act(f)
            assert self.middleware.executed
            self.middleware.executed = False

    @pytest.mark.usefixtures("setup_middleware_checking_being_invoked")
    async def test_act_doesnt_act_on_invalid_filenames(self):
        filenames = [
            "test.pdf",
            "test.py",
            "ABC test.pdf",
            "AB test.pdf",
            "PH.pdf",
            ".PH HA 22-06-2021.pdf",
            "_PH HA 22-06-2021.pdf"
        ]

        for f in filenames:
            await self.middleware.act(f)
            assert not self.middleware.executed
            self.middleware.executed = False

    @pytest.mark.usefixtures("setup_subject_compression_middleware")
    async def test_act_subject_valid_raises_not_implemented_error(self):
        with pytest.raises(NotImplementedError):
            await self.middleware.act_subject_valid("PH HA 22-06-2021.pdf")


@pytest.mark.usefixtures("setup_middleware")
class TestFlashLightsInHomeAssistantMiddleware:

    @pytest.fixture
    def setup_middleware(self, logger):
        self.middleware = FlashLightsInHomeAssistantMiddleware(logger)

    @pytest.mark.asyncio
    async def test_tries_to_flash_lights_in_home_assistant(self, httpx_mock):
        httpx_mock.add_response(
            method="POST", url=HASS_BASE_URL
            + "/api/services/script/flash_miguels_room")

        await self.middleware.act("test.pdf")

        req = httpx_mock.get_request()
        assert req.headers["authorization"] == "Bearer " + HASS_TOKEN


@pytest.mark.usefixtures("setup_middleware")
class TestChangesStatusInThings:

    @pytest.fixture
    def setup_middleware(self, logger):
        self.middleware = ChangeStatusInThingsMiddleware(logger)

    @pytest.mark.asyncio
    async def test_tries_to_check_homework_in_things(self, httpx_mock):
        httpx_mock.add_response(
            method="POST",
            url=THINGS_SERVER_URL + "/api/v1/markhomeworkasdone?subject=PH")

        # don't need to check manually as pytest-httpx automatically raises
        # an error when mock endpoints remain uncontacted.
        await self.middleware.act("PH HA 22-06-2021.pdf")


# referring to this class being in this module: feels like this is more at home here
# than in test_compression_manager

@pytest.mark.asyncio
class TestMiddlewareIntegration(
        tests.test_compression_manager.AnyTestCase):

    @ pytest.fixture
    def setup_middleware_checking_being_invoked(self, logger):
        class MiddlewareCheckingBeingInvoked(
                CompressionMiddleware):
            def __init__(self, logger):
                super().__init__(logger)
                self.files_invoked_for = []

            async def act(self, filename):
                self.files_invoked_for.append(filename)
        self.middleware = MiddlewareCheckingBeingInvoked(logger)
        self.manager.register_middleware(self.middleware)

    @ pytest.fixture
    def setup_faulty_middleware(self, logger):
        class FaultyMiddleware(CompressionMiddleware):
            async def act(self, filename):
                raise Exception("Better handle this!")
        self.middleware = FaultyMiddleware(logger)
        self.manager.register_middleware(self.middleware)

    @ pytest.mark.usefixtures("do_setup",
                              "configure_mock_responses",
                              "setup_middleware_checking_being_invoked")
    async def test_compression_middleware_being_called_by_compression_manager(
            self, fs):
        files = [
            "test.pdf",
            "PH HA 22-06-2021.pdf",
            "PH Klausurvorbereitung 4. Klausur.pdf",
            ".PH Klausurvorbereitung 4. Klausur.pdf",
            "_PH Klausurvorbereitung 4. Klausur.pdf",
            "_PH HA 22-06-2021.pdf",
            "something.txt"
        ]
        for f in files:
            tests.test_compression_manager.create_file(fs, f)

        await self.manager.compress_directory(HOMEWORK_DIR)

        assert self.middleware.files_invoked_for == [os.path.join(
            HOMEWORK_DIR, fname) for fname in files[:3]]

    @ pytest.mark.usefixtures("do_setup",
                              "configure_mock_responses",
                              "setup_faulty_middleware")
    async def test_exceptions_in_middleware_handled_appropriately(self, fs):
        f = "PH HA 22-06-2021.pdf"
        tests.test_compression_manager.create_file(fs, f)

        print(f"Homework_dir: '{HOMEWORK_DIR}'")
        print(f"HASS_URL: '{HASS_BASE_URL}'")
        print(f"Things URL: '{THINGS_SERVER_URL}'")
        await self.manager.compress_directory(HOMEWORK_DIR)
