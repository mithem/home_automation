import os
import fileloghelper
import config
import asyncio
import argparse

import CompressionMiddleware
from ArchiveManager import abbr_to_subject
from CompressionMiddleware import (
    FlashLightsInHomeAssistantMiddleware,
    ChangeStatusInThingsMiddleware
)

config.load_dotenv()

root = "/volume2/Hausaufgaben/HAs"
blacklist = ["@eaDir"]
blacklist_beginnings = ["Scan ", ".", "_"]
blacklist_endings = [".small.pdf"]
home_assistant_token = os.environ.get("HASS_TOKEN")
home_assistant_url = os.environ.get("HASS_BASE_URL")
things_server_url = os.environ.get("THINGS_SERVER_URL")
timeout = 1
subject_abbrs = abbr_to_subject.keys()


class LoopBreakingException(Exception):
    pass


class CompressionManager:
    def __init__(self, debug=False, testing=False):
        self.logger = fileloghelper.Logger(os.path.join(
            os.environ.get("LOG_DIR"), "CompressionManager.log"),
            autosave=debug)
        if not testing:
            # introduces weird fomatting in pytest
            self.logger.header(True, True)
        self.debug = debug
        self.middleware = []

    async def compress_directory(self, directory: str):

        def skip(f: str):
            self.logger.debug(
                f"Skipping {path} as it doesn't qualify for \
                                compression")

        self.logger.context = "compressing"
        self.logger.debug(f"Compressing directory '{directory}'")
        dirlist = os.listdir(directory)

        for f in dirlist:
            path = os.path.join(directory, f)
            try:
                if os.path.isdir(path):
                    if f not in blacklist:
                        await self.compress_directory(path)
                elif f.endswith(".pdf"):
                    if f.endswith(".small.pdf"):
                        fname = f[:-10]
                    else:
                        fname = ".".join(f.split(".")[:-1])
                    try:
                        tf = open(os.path.join(directory, f), "r+")
                        tf.close()
                    except (FileNotFoundError, PermissionError):
                        continue

                    if fname in blacklist or fname + ".small.pdf" in dirlist:
                        skip(fname)
                        continue
                    try:
                        for beg in blacklist_beginnings:
                            if fname.startswith(beg):
                                skip(fname)
                                raise LoopBreakingException()
                        for end in blacklist_endings:
                            if f.endswith(end):
                                skip(fname)
                                raise LoopBreakingException()
                    except LoopBreakingException:
                        continue

                    for m in self.middleware:
                        task = asyncio.create_task(
                            m.act(f))
                        if self.debug:
                            self.logger.debug(
                                "Invoking middleware: '"
                                + m.__class__.__name__
                                + "' for '"
                                + path
                                + "'")
                        try:
                            await task
                        except Exception as e:
                            self.logger.handle_exception(e)

                    self.logger.info(f"Compressing '{path}'")
                    cmd = f"gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
                            -dPDFSETTINGS=/ebook -dNOPAUSE -dBATCH \
                            -sOutputFile='{path[:-4]}.small.pdf' '{path}'"
                    os.system(cmd)
            except KeyError as e:
                self.logger.handle_exception(e)

    def clean_up_directory(self, directory: str):
        """Clean files added by another service, like ".M HA" etc.\
                (might come from Documents by Readdle or so)"""
        self.logger.context = "clean_up"
        self.logger.debug(f"Cleaning up directory: {directory}")
        for f in os.listdir(directory):
            if f.startswith(".") or f.startswith("_"):
                path = os.path.join(directory, f)
                try:
                    length = len(f.split(" ")[0])
                    if length == 2 or length == 3:
                        os.remove(path)
                        self.logger.success(f"Removed {path}")
                except KeyError:
                    continue
                except Exception as e:
                    self.logger.handle_exception(e)

    def register_middleware(self, middleware: CompressionMiddleware):
        self.middleware.append(middleware)
        self.logger.info("Registered middleware "
                         + f"'{middleware.__class__.__name__}'", self.debug)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", "--verbose", "-d", "-v",
                        action="store_true", help="debug/verbose mode")
    args = parser.parse_args()

    middleware = [
        FlashLightsInHomeAssistantMiddleware,
        ChangeStatusInThingsMiddleware
    ]
    manager = CompressionManager(args.debug)

    [manager.register_middleware(m(manager.logger)) for m in middleware]

    await manager.compress_directory(root)

    manager.clean_up_directory(root)

if __name__ == "__main__":
    asyncio.run(main())
