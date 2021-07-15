import pytest
import httpx
import os
from fileloghelper import Logger

import test_CompressionManager
from Home_Automation.CompressionMiddleware import (
    CompressionMiddleware,
    SubjectCompressionMiddleware,
    FlashLightsInHomeAssistantMiddleware,
    ChangeStatusInThingsMiddleware,
    InvalidResponseError
)
from Home_Automation.CompressionManager import root
# pytest needs this to be imported in this module
from test_CompressionManager import configure_mock_responses

_logger = Logger()
home_assistant_url = os.environ.get("HASS_BASE_URL")
home_assistant_token = os.environ.get("HASS_TOKEN")
things_server_url = os.environ.get("THINGS_SERVER_URL")


@pytest.fixture
def logger():
    return logger


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
            "PH.pdf"
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
            method="POST", url=home_assistant_url
            + "/api/services/script/flash_miguels_room")

        await self.middleware.act("test.pdf")

        req = httpx_mock.get_request()
        assert req.headers["authorization"] == "Bearer " + home_assistant_token


@pytest.mark.usefixtures("setup_middleware")
class TestChangesStatusInThings:

    @pytest.fixture
    def setup_middleware(self, logger):
        self.middleware = ChangeStatusInThingsMiddleware(logger)

    @pytest.mark.asyncio
    async def test_tries_to_check_homework_in_things(self, httpx_mock):
        httpx_mock.add_response(
            method="POST",
            url=things_server_url + "/api/v1/markhomeworkasdone?subject=PH")

        # don't need to check manually as pytest-httpx automatically raises
        # an error when mock endpoints remain uncontacted.
        await self.middleware.act("PH HA 22-06-2021.pdf")


# referring this class in this module: feels like this is more at home here
# than in test_CompressionManager

@pytest.mark.asyncio
class TestMiddlewareIntegration(
        test_CompressionManager.AnyTestCase):

    @pytest.fixture
    def setup_middleware_checking_being_invoked(self, logger):
        class MiddlewareCheckingBeingInvoked(
                CompressionMiddleware):
            def __init__(self, logger):
                super().__init__(logger)
                self.files_invoked_for = []

            async def act(self, filename):
                self.files_invoked_for.append(filename)
        self.middleware = \
            MiddlewareCheckingBeingInvoked(logger)
        self.manager.register_middleware(self.middleware)

    @pytest.fixture
    def setup_faulty_middleware(self, logger):
        class FaultyMiddleware(CompressionMiddleware):
            async def act(self, filename):
                raise Exception("Better handle this!")
        self.middleware = FaultyMiddleware(logger)
        self.manager.register_middleware(self.middleware)

    @pytest.mark.usefixtures("do_setup",
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
            test_CompressionManager.create_file(fs, f)

        await self.manager.compress_directory(root)

        assert self.middleware.files_invoked_for == files[:3]

    @pytest.mark.usefixtures("do_setup",
                             "configure_mock_responses",
                             "setup_faulty_middleware")
    async def test_exceptions_in_middleware_handled_appropriately(self, fs):
        f = "PH HA 22-06-2021.pdf"
        test_CompressionManager.create_file(fs, f)

        await self.manager.compress_directory(root)
