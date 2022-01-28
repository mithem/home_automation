"""Manages compressing files."""
import argparse
import asyncio
import os
import sys
from typing import List, Union

import fileloghelper
from home_automation import config
from home_automation.archive_manager import ABBR_TO_SUBJECT
from home_automation.compression_middleware import (
    ChangeStatusInThingsMiddleware, CompressionMiddleware,
    FlashLightsInHomeAssistantMiddleware
)

config.load_dotenv()

BLACKLIST = ["@eaDir"]
BLACKLIST_BEGINNINGS = ["Scan ", ".", "_", "Scanned Document"]
BLACKLIST_ENDINGS = [".small.pdf"]
SUBJECT_ABBRS = ABBR_TO_SUBJECT.keys()
LOG_DIR = ""
EXTRA_COMPRESS_DIRS = os.environ.get("EXTRA_COMPRESS_DIRS", "").split(";")


def load_envvars():
    """Load constants from environment."""
    for key in ["LOG_DIR"]:
        setattr(sys.modules[__name__], key, os.environ[key])


class LoopBreakingException(Exception):
    """Internal. Used to break a loop."""


class CompressionManager:
    """Manages compressing files."""

    def __init__(self, debug=False, testing=False):
        self.logger = fileloghelper.Logger(os.path.join(
            LOG_DIR, "compression_manager.log"), autosave=debug)
        self.homework_dir = str(os.environ.get("HOMEWORK_DIR"))
        if not testing:
            # introduces weird fomatting in pytest
            self.logger.header(True, True)
        self.debug = debug
        self.middleware = []

    async def compress_directory(self, directory: str = None):
        """For each file or directory in `directory`, compress it."""
        if directory:
            dir_to_compress = directory
        else:
            dir_to_compress = self.homework_dir

        self.logger.context = "compressing"
        self.logger.debug(f"Compressing directory '{dir_to_compress}'")
        dirlist = os.listdir(dir_to_compress)

        for fname in dirlist:
            path = os.path.join(dir_to_compress, fname)
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
                            -sOutputFile='{path.replace('.pdf', '.small.pdf')}' '{path}'"
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
            with open(path, "r+", encoding="utf-8"):
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

    def clean_up_directory(self, directory: str = None):
        """Clean files added by another service, like ".M HA" etc.\
                (might come from Documents by Readdle or so)"""
        if directory:
            dir_to_compress = directory
        else:
            dir_to_compress = self.homework_dir

        self.logger.context = "clean_up"
        self.logger.debug(f"Cleaning up directory: {directory}")
        for fname in os.listdir(dir_to_compress):
            if fname.startswith(".") or fname.startswith("_"):
                path = os.path.join(dir_to_compress, fname)
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


async def main(arguments: Union[str, List[str]] = None):
    """What could this do?"""
    if isinstance(arguments, str):
        arguments = arguments.split(" ")
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v",
            action="store_true", help="verbose mode")
    args = parser.parse_args(arguments)

    config.load_dotenv()
    load_envvars()

    insecure_https = bool(int(os.environ.get("INSECURE_HTTPS", 0)))

    manager = CompressionManager(args.verbose)

    middleware = [
        FlashLightsInHomeAssistantMiddleware(manager.logger, insecure_https),
        ChangeStatusInThingsMiddleware(manager.logger)
    ]

    for midware in middleware:
        manager.register_middleware(midware)

    await manager.compress_directory()

    for directory in EXTRA_COMPRESS_DIRS:
        await manager.compress_directory(directory)

    manager.clean_up_directory()

def run_main():
    """Run the main coroutine via asyncio.run."""
    asyncio.run(main())

if __name__ == "__main__":
    run_main()
