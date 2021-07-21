"""Manages compressing files."""
import argparse
import asyncio
import os
from typing import List

import fileloghelper
from home_automation import config
from home_automation.archive_manager import ABBR_TO_SUBJECT
from home_automation.compression_middleware import (
    ChangeStatusInThingsMiddleware, CompressionMiddleware,
    FlashLightsInHomeAssistantMiddleware
)

config.load_dotenv()

ROOT_DIR = "/volume2/Hausaufgaben/HAs"
BLACKLIST = ["@eaDir"]
BLACKLIST_BEGINNINGS = ["Scan ", ".", "_"]
BLACKLIST_ENDINGS = [".small.pdf"]
HOME_ASSISTANT_URL = os.environ.get("HASS_BASE_URL")
HOME_ASSISTANT_TOKEN = os.environ.get("HASS_TOKEN")
THINGS_SERVER_URL = os.environ.get("THINGS_SERVER_URL")
SUBJECT_ABBRS = ABBR_TO_SUBJECT.keys()


class LoopBreakingException(Exception):
    """Internal. Used to break a loop."""


class CompressionManager:
    """Manages compressing files."""

    def __init__(self, debug=False, testing=False):
        self.logger = fileloghelper.Logger(os.path.join(
            os.environ.get("LOG_DIR"), "CompressionManager.log"),
            autosave=debug)
        if not testing:
            # introduces weird fomatting in pytest
            self.logger.header(True, True)
        self.debug = debug
        self.middleware = []

    async def compress_directory(self, directory: str):  # pylint: disable=no-self-use
        """For each file or directory in `directory`, compress it."""


        self.logger.context = "compressing"
        self.logger.debug(f"Compressing directory '{directory}'")
        dirlist = os.listdir(directory)

        for fname in dirlist:
            path = os.path.join(directory, fname)
            try:
                if os.path.isdir(path):
                    if fname not in BLACKLIST:
                        await self.compress_directory(path)
                elif path.endswith(".pdf"):
                    if path.endswith(".small.pdf"):
                        fname = fname[:-10]
                    else:
                        fname = ".".join(fname.split(".")[:-1])
                    if self.file_should_be_skipped(path, fname, dirlist):
                        continue

                    await self.apply_middleware(path)

                    self.logger.info(f"Compressing '{path}'")
                    cmd = f"gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
                            -dPDFSETTINGS=/ebook -dNOPAUSE -dBATCH \
                            -sOutputFile='{fname}.small.pdf' '{path}'"
                    os.system(cmd)
            except KeyError as error:
                self.logger.handle_exception(error)

    def file_should_be_skipped(self, path: str, fname: str, dirlist: List[str]):
        """Decide, whether file should be skipped.
        Deal with logging and return True/False respectively."""
        def skip(path: str):
            self.logger.debug(
                f"Skipping {path} as it doesn't qualify for \
                                compression")

        if fname in BLACKLIST or fname + ".small.pdf" in dirlist:
            skip(path)
            return True
        try:
            for beg in BLACKLIST_BEGINNINGS:
                if fname.startswith(beg):
                    raise LoopBreakingException()
            for end in BLACKLIST_ENDINGS:
                if fname.endswith(end):
                    raise LoopBreakingException()
        except LoopBreakingException:
            skip(path)
            return True
        try:
            with open(path, "r+"):
                pass
        except (FileNotFoundError, PermissionError) as error:
            self.logger.handle_exception(error)
            return True
        return False

    async def apply_middleware(self, path: str):
        """Let all middleware act on `path`."""
        for middleware in self.middleware:
            task = asyncio.create_task(
                middleware.act(path))
            if self.debug:
                self.logger.debug(
                    "Invoking middleware: '"
                    + middleware.__class__.__name__
                    + "' for '"
                    + path
                    + "'")
            try:
                await task
            except Exception as error:  # pylint: disable=broad-except
                self.logger.handle_exception(error)

    def clean_up_directory(self, directory: str):
        """Clean files added by another service, like ".M HA" etc.\
                (might come from Documents by Readdle or so)"""
        self.logger.context = "clean_up"
        self.logger.debug(f"Cleaning up directory: {directory}")
        for fname in os.listdir(directory):
            if fname.startswith(".") or fname.startswith("_"):
                path = os.path.join(directory, fname)
                try:
                    length = len(fname.split(" ")[0])
                    if length in (2, 3):
                        os.remove(path)
                        self.logger.success(f"Removed {path}")
                except KeyError:
                    continue
                except Exception as error:  # pylint: disable=broad-except
                    self.logger.handle_exception(error)

    def register_middleware(self, middleware: CompressionMiddleware):
        """Register a new `CompressionMiddleware` to be called whenever a new file gets compressed.
        Required to be actually useful."""
        self.middleware.append(middleware)
        self.logger.info("Registered middleware "
                         + f"'{middleware.__class__.__name__}'", self.debug)


async def main():
    """What could this do?"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v",
                        action="store_true", help="verbose mode")
    args = parser.parse_args()

    middleware = [
        FlashLightsInHomeAssistantMiddleware,
        ChangeStatusInThingsMiddleware
    ]
    manager = CompressionManager(args.verbose)

    for midware in middleware:
        manager.register_middleware(
            midware(manager.logger))  # pylint: disable=multiple-statements
    await manager.compress_directory(ROOT_DIR)

    manager.clean_up_directory(ROOT_DIR)

if __name__ == "__main__":
    asyncio.run(main())
