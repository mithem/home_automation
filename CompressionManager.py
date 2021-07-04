import os
import grequests
import fileloghelper
import config

config.load_dotenv()

root = "/volume2/Hausaufgaben/HAs"
blacklist = ["@eaDir"]
home_assistant_token = os.environ.get("HASS_TOKEN")
home_assistant_url = os.environ.get("HASS_BASE_URL")
things_server_url = os.environ.get("THINGS_SERVER_URL")
timeout = 10


class CompressionManager:
    def __init__(self, debug=False):
        self.logger = fileloghelper.Logger(os.path.join(
            os.environ.get("LOG_DIR"), "CompressionManager.log"),
            autosave=debug)
        self.logger.header(True, True)
        self.debug = debug

    def clean_up_directory(self, directory: str):
        """Clean files added by another service, like ".M HA" etc.\
                (might come from Documents by Readdle or so)"""
        self.logger.context = "clean_up"
        self.logger.debug(f"Cleaning up directory: {directory}")
        for f in os.listdir(directory):
            if f.startswith(".") or f.startswith("_"):
                try:
                    length = len(f.split(" ")[0])
                    if length == 2 or length == 3:
                        os.remove(f)
                        self.logger.success(f"Removed {f}")
                except KeyError:
                    continue
                except Exception as e:
                    self.logger.handle_exception(e)

    def flash_lights_in_home_assistant(self):
        def handle_response(response):
            try:
                if not response.ok:
                    raise Exception(response.text)
                else:
                    self.logger.success("Flashed lights.")
            except Exception as e:
                self.logger.handle_exception(e)
        try:
            self.logger.context = "flash_lights_in_home_assistant"
            self.logger.debug("Trying to flash lights")
            h = {"Authorization": "Bearer " + home_assistant_token}
            action_item = grequests.post(
                home_assistant_url + "/api/services/script/flash_miguels_room",
                headers=h, timeout=timeout)
            responses = grequests.map([action_item])
            for r in responses:
                handle_response(r)
        except Exception as e:
            self.logger.handle_exception(e)

    def change_status_in_things(self, subject: str):
        def handle_response(r):
            if r.ok:
                self.logger.success(f"Checked homework ({subject}) in Things.")
            else:
                self.logger.error(f"Response: {r}")
        self.logger.context = "change_status_in_things"
        self.logger.debug("Trying to change status in things")
        try:
            action_item = grequests.post(things_server_url + f"/api/v1/\
    markhomeworkasdone?subject={subject}", timeout=timeout)
            responses = grequests.map([action_item])
            for r in responses:
                handle_response(r)
        except Exception as e:
            self.logger.handle_exception(e)

    def compress_directory(self, directory: str):
        self.logger.context = "compressing"
        self.logger.debug(f"Compressing directory '{directory}'")
        dirlist = os.listdir(directory)
        for f in dirlist:
            if os.path.isdir(f) or os.path.islink(f):
                if f not in blacklist:
                    self.compress_directory(f)
            elif f.endswith(".pdf"):
                fname = f.replace(".pdf", "")
                try:
                    tf = open(f"/volume2/Hausaufgaben/HAs/{f}", "r+")
                    tf.close()
                except (FileNotFoundError, PermissionError):
                    continue
                path = root + "/" + fname
                if not (fname.startswith("Scan ") or fname == "" or
                        f.endswith(".small.pdf") or
                        fname + ".small.pdf" in dirlist or f in blacklist):
                    subject = fname.split(" ")[0].upper()
                    self.change_status_in_things(subject)
                    self.flash_lights_in_home_assistant()
                    self.logger.info(f"Compressing '{path}'")
                    cmd = f"gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
                            -dPDFSETTINGS=/ebook -dNOPAUSE -dBATCH \
                            -sOutputFile='{path}.small.pdf' '{path}.pdf'"
                    os.system(cmd)
                else:
                    self.logger.debug(
                        f"Skipping {path} as it doesn't qualify for \
                                compression")
        self.clean_up_directory(directory)


if __name__ == "__main__":
    manager = CompressionManager()
    manager.compress_directory(root)
