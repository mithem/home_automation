import os
import httpx
import fileloghelper
import config
import asyncio
from ArchiveManager import abbr_to_subject

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

                    self.logger.info(f"Compressing '{path}'")
                    cmd = f"gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
                            -dPDFSETTINGS=/ebook -dNOPAUSE -dBATCH \
                            -sOutputFile='{path}.small.pdf' '{path}.pdf'"
                    subject = fname.split(" ")[0].upper()
                    if subject in subject_abbrs:
                        await self.change_status_in_things(subject)
                        await self.flash_lights_in_home_assistant()
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

    def _handle_response(self, response: httpx.Response, whenSuccessful: str):
        """Check if response is OK and, if so, log a success message.
        Otherwise log the error."""
        try:
            if not response.status_code == 200:
                raise Exception(response.text)
            else:
                self.logger.success(whenSuccessful)
        except Exception as e:
            self.logger.handle_exception(e)

    async def flash_lights_in_home_assistant(self):
        try:
            self.logger.context = "flash_lights_in_home_assistant"
            self.logger.debug("Trying to flash lights")
            h = {"Authorization": "Bearer " + home_assistant_token}
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    home_assistant_url
                    + "/api/services/script/flash_miguels_room",
                    headers=h, timeout=timeout)
            self._handle_response(r, "Flashed lights.")
        except Exception as e:
            self.logger.handle_exception(e)

    async def change_status_in_things(self, subject: str):
        self.logger.context = "change_status_in_things"
        self.logger.debug("Trying to change status in things")
        if subject.startswith(".") or subject.startswith("_"):
            return
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(things_server_url +
                                      "/api/v1/markhomeworkasdone?"
                                      + f"subject={subject}",
                                      timeout=timeout)
            self._handle_response(
                r, f"Checked homework ({subject}) in Things.")
        except Exception as e:
            self.logger.handle_exception(e)


async def main():
    manager = CompressionManager()
    await manager.compress_directory(root)
    manager.clean_up_directory(root)

if __name__ == "__main__":
    asyncio.run(main())
