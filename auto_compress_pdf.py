import os
import grequests
import fileloghelper
import dotenv

dotenv.load_dotenv()

root = "/volume2/Hausaufgaben/HAs"
blacklist = ["@eaDir"]
home_assistant_token = os.environ("HASS_TOKEN")
home_assistant_base_url = os.environ("HASS_BASE_URL")
things_server_url = os.environ("THINGS_SERVER_URL")
timeout = 10

logger = fileloghelper.Logger("/volume2/administration/auto_compress_pdf.log",
                              autosave=True)


def clean_up_directory(directory: str):
    """Clean files added by another service, like ".M HA" etc. (might come from Documents by Readdle or so)"""
    global logger
    logger.context = "clean_up"
    logger.debug(f"Cleaning up directory: {directory}")
    for f in os.listdir(directory):
        if f.startswith(".") or f.startswith("_"):
            try:
                length = len(f.split(" ")[0])
                if length == 2 or length == 3:
                    os.remove(f)
                    logger.success(f"Removed {f}")
            except KeyError:
                continue
            except Exception as e:
                logger.handle_exception(e)


def flash_lights_in_home_assistant():
    def handle_response(response):
        try:
            if not response.ok:
                raise Exception(response.text)
            else:
                logger.success("Flashed lights.")
        except Exception as e:
            logger.handle_exception(e)
    try:
        global logger
        logger.context = "flash_lights_in_home_assistant"
        logger.debug("Trying to flash lights")
        h = {"Authorization": "Bearer " + home_assistant_token}
        action_item = grequests.post(
            home_assistant_base_url + "/api/services/script/flash_miguels_room", headers=h, timeout=timeout)
        responses = grequests.map([action_item])
        for r in responses:
            handle_response(r)
    except Exception as e:
        logger.handle_exception(e)


def change_status_in_things(subject: str):
    def handle_response(r):
        if r.ok:
            logger.success(f"Checked homework ({subject}) in Things.")
        else:
            logger.error(f"Response: {r}")
    global logger
    logger.context = "change_status_in_things"
    logger.debug("Trying to change status in things")
    try:
        action_item = grequests.post(things_server_url + f"/api/v1/\
markhomeworkasdone?subject={subject}", timeout=timeout)
        responses = grequests.map([action_item])
        for r in responses:
            handle_response(r)
    except Exception as e:
        logger.handle_exception(e)


def compress_directory(directory: str):
    global logger
    logger.context = "compressing"
    logger.debug(f"Compressing directory '{directory}'")
    dirlist = os.listdir(directory)
    for f in dirlist:
        if os.path.isdir(f) or os.path.islink(f):
            if f not in blacklist:
                compress_directory(f)
        elif f.endswith(".pdf"):
            fname = f.replace(".pdf", "")
            try:
                tf = open(f"/volume2/Hausaufgaben/HAs/{f}", "r+")
                tf.close()
            except:
                continue
            path = root + "/" + fname
            if not (fname.startswith("Scan ") or fname == "" or
                    f.endswith(".small.pdf") or
                    fname + ".small.pdf" in dirlist or f in blacklist):
                subject = fname.split(" ")[0].upper()
                change_status_in_things(subject)
                flash_lights_in_home_assistant()
                logger.info(f"Compressing '{path}'")
                cmd = f"gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
                        -dPDFSETTINGS=/ebook -dNOPAUSE -dBATCH \
                        -sOutputFile='{path}.small.pdf' '{path}.pdf'"
                os.system(cmd)
            else:
                logger.debug(
                    f"Skipping {path} as it doesn't qualify for compression")
    clean_up_directory(directory)


if __name__ == "__main__":
    logger.header(True, True)
    compress_directory(root)
