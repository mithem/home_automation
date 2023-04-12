"""The middleware framework used to act on each file getting compressed."""
# pylint: disable=global-statement
import os
import re

import fileloghelper
import httpx

from home_automation.constants import ABBR_TO_SUBJECT
from home_automation import config as haconfig
from home_automation.config import ConfigError

TIMEOUT = 10
SUBJECT_ABBRS = ABBR_TO_SUBJECT.keys()


class InvalidResponseError(Exception):
    """Invalid response (who would have guessed??)"""


class InvalidFilenameError(Exception):
    """1-2-3, what might this be?"""


class CompressionMiddleware:
    """Middleware's `.act` method is called for each file (-path) being compressed.
    For example, it can be used to communicate with other services.
    Each coroutine is executed separately."""

    logger: fileloghelper.Logger
    config: haconfig.Config

    def __init__(self, config: haconfig.Config, logger: fileloghelper.Logger):
        self.config = config
        self.logger = logger

    async def act(self, path: str):  # pylint: disable=R0102,unused-argument
        """Act on the file being compressed."""
        raise NotImplementedError()

    def handle_response(self, response: httpx.Response):  # pylint: disable=R0102
        """Just throw an exception if something isn't right!"""
        if not response.status_code == 200:
            raise InvalidResponseError(response.text)


class SubjectCompressionMiddleware(CompressionMiddleware):
    """A Middleware that ensures that the name of the file compressed
    starts with a valid subject abbreviation."""

    async def act(self, path: str):
        _, filename = os.path.split(path)
        if filename.split(" ")[0].upper() in SUBJECT_ABBRS:
            await self.act_subject_valid(path)

    async def act_subject_valid(self, path: str):
        """Act on the file being compressed having a verified subject identifiable."""
        raise NotImplementedError()


class FlashLightsInHomeAssistantMiddleware(CompressionMiddleware):
    """Responsible for trying to encourage HomeAssistant to flash lights."""

    async def act(self, path: str):
        await self.flash_lights_in_home_assistant()

    async def flash_lights_in_home_assistant(self):
        """What could be tried here?"""
        if (
            not self.config.home_assistant
            or not self.config.home_assistant.token
            or not self.config.home_assistant.url
        ):
            raise ConfigError("Home Assistant data not configured.")
        headers = {"Authorization": "Bearer " + self.config.home_assistant.token}
        async with httpx.AsyncClient(
            verify=not self.config.home_assistant.insecure_https
        ) as client:
            response = await client.post(
                self.config.home_assistant.url
                + "/api/services/script/flash_miguels_room",
                headers=headers,
                timeout=TIMEOUT,
            )
        self.handle_response(response)


class ChangeStatusInThingsMiddleware(SubjectCompressionMiddleware):
    """Responsible for trying to encourage things_server to check the appropriate homework."""

    async def act_subject_valid(self, path: str):
        homework_dir_pattern_group = re.escape(self.config.homework_dir)
        pattern = rf"^{homework_dir_pattern_group}/.+$"
        match = re.match(pattern, path)
        if not match:
            return
        await self.change_status_in_things(path)

    async def change_status_in_things(self, path: str):
        """What could be tried here?"""
        if not self.config.things_server:
            raise ConfigError("Things server data not configured.")
        if not self.config.things_server.url:
            raise ConfigError("Things server URL not configured.")
        _, filename = os.path.split(path)
        subject = filename.split(" ")[0].upper()
        async with httpx.AsyncClient(
            verify=not self.config.things_server.insecure_https
        ) as client:
            response = await client.post(
                self.config.things_server.url
                + "/api/v1/markhomeworkasdone?"
                + f"subject={subject}",
                timeout=TIMEOUT,
            )
        self.handle_response(response)
