"""The middleware framework used to act on each file getting compressed."""
# pylint: disable=global-statement
import os

import fileloghelper
import httpx

from home_automation.archive_manager import ABBR_TO_SUBJECT
from home_automation import config

config.load_dotenv()
HOME_ASSISTANT_URL = os.environ.get("HASS_BASE_URL")
HOME_ASSISTANT_TOKEN = os.environ.get("HASS_TOKEN")
THINGS_SERVER_URL = os.environ.get("THINGS_SERVER_URL")
TIMEOUT = 10
SUBJECT_ABBRS = ABBR_TO_SUBJECT.keys()

class InvalidResponseError(Exception):
    """Invalid response (who would have guessed??)"""


class CompressionMiddleware:
    """Middleware's `.act` method is called for each file (-path) being compressed.
    For example, it can be used to communicate with other services.
    Each coroutine is executed separately."""

    def __init__(self, logger: fileloghelper.Logger):
        self.logger = logger

    async def act(self, path: str): #pylint: disable=no-self-use
        """Act on the file being compressed."""
        raise NotImplementedError()

    def handle_response(self, response: httpx.Response): # pylint: disable=no-self-use
        """Just throw an exception if something isn't right!"""
        if not response.status_code == 200:
            raise InvalidResponseError(response.text)


class SubjectCompressionMiddleware(CompressionMiddleware):
    """A Middleware that ensures that the name of the file compressed
    starts with a valid subject abbreviation."""
    async def act(self, path: str):
        _, filename = os.path.split(path)
        try:
            if filename.split(" ")[0].upper() in SUBJECT_ABBRS:
                await self.act_subject_valid(filename)
        except Exception as error: # pylint: disable=broad-except
            self.logger.handle_exception(error)

    async def act_subject_valid(self, filename: str):
        """Act on the file being compressed having a verified subject identifiable."""
        raise NotImplementedError()


class FlashLightsInHomeAssistantMiddleware(CompressionMiddleware):
    """Responsible for trying to encourage HomeAssistant to flash lights."""
    async def act(self, path: str):
        await self.flash_lights_in_home_assistant()

    async def flash_lights_in_home_assistant(self):
        """What could be tried here?"""
        headers = {"Authorization": "Bearer " + HOME_ASSISTANT_TOKEN}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                HOME_ASSISTANT_URL
                + "/api/services/script/flash_miguels_room",
                headers=headers, timeout=TIMEOUT)
        self.handle_response(response)


class ChangeStatusInThingsMiddleware(SubjectCompressionMiddleware):
    """Responsible for trying to encourage things_server to check the appropriate homework."""
    async def act_subject_valid(self, filename: str):
        await self.change_status_in_things(filename)

    async def change_status_in_things(self, filename):
        """What could be tried here?"""
        subject = filename.split(" ")[0].upper()
        if subject.startswith(".") or subject.startswith("_"):
            raise Exception("Subject starts with '.' or '_'. That's invalid.")
        async with httpx.AsyncClient() as client:
            response = await client.post(THINGS_SERVER_URL +
                                  "/api/v1/markhomeworkasdone?"
                                  + f"subject={subject}",
                                  timeout=TIMEOUT)
        self.handle_response(response)
