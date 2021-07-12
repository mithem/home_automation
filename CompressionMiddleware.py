from fileloghelper import Logger
from functools import wraps
from typing import Callable, Union
import os
import httpx

from ArchiveManager import abbr_to_subject

home_assistant_url = os.environ.get("HASS_BASE_URL")
home_assistant_token = os.environ.get("HASS_TOKEN")
things_server_url = os.environ.get("THINGS_SERVER_URL")
timeout = 10
subject_abbrs = abbr_to_subject.keys()
logger = None


class InvalidResponseError(Exception):
    pass


class CompressionMiddleware:
    """Middleware's `.act` method is called for each file being compressed.
    For example, it can be used to communicate with other services.
    Each coroutine is executed separately."""

    def __init__(self, logger_: Logger):
        global logger
        logger = logger_

    async def act(self, filename: str):
        raise NotImplementedError()

    def handle_response(self, response: httpx.Response):
        """Just throw an exception if something isn't right!"""
        if not response.status_code == 200:
            raise InvalidResponseError(response.text)


class SubjectCompressionMiddleware(CompressionMiddleware):
    """A Middleware that ensures that the name of the file compressed
    starts with a valid subject abbreviation."""
    async def act(self, filename: str):
        global logger
        try:
            if filename.split(" ")[0].upper() in subject_abbrs:
                await self.act_subject_valid(filename)
        except Exception as e:
            logger.handle_exception(e)

    async def act_subject_valid(self, filename: str):
        raise NotImplementedError()


class FlashLightsInHomeAssistantMiddleware(CompressionMiddleware):
    async def act(self, filename: str):
        await self.flash_lights_in_home_assistant()

    async def flash_lights_in_home_assistant(self):
        h = {"Authorization": "Bearer " + home_assistant_token}
        async with httpx.AsyncClient() as client:
            r = await client.post(
                home_assistant_url
                + "/api/services/script/flash_miguels_room",
                headers=h, timeout=timeout)
        self.handle_response(r)


class ChangeStatusInThingsMiddleware(SubjectCompressionMiddleware):
    async def act_subject_valid(self, filename: str):
        await self.change_status_in_things(filename)

    async def change_status_in_things(self, filename):
        subject = filename.split(" ")[0].upper()
        if subject.startswith(".") or subject.startswith("_"):
            raise Exception("Subject starts with '.' or '_'. That's invalid.")
        async with httpx.AsyncClient() as client:
            r = await client.post(things_server_url +
                                  "/api/v1/markhomeworkasdone?"
                                  + f"subject={subject}",
                                  timeout=timeout)
        self.handle_response(r)
