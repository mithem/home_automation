import re
import datetime
import fileloghelper
import os
import yagmail
import argparse
import config

month_to_dir = {
    1: "Januar",
    2: "Feburar",
    3: "März",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember"
}

abbr_to_subject = {
    "D": "Deutsch",
    "E": "Englisch",
    "EK": "Erdkunde",
    "GE": "Geschichte",
    "IF": "Informatik",
    "K": "Kunst",
    "M": "Mathe",
    "PL": "Philosophie",
    "PSE": "Software Engineering",
    "PH": "Physik",
    "SW": "SoWi",
    "SP": "Sport"
}

config.load_dotenv()

blacklist_files = [".DS_Store", "@eaDir"]
blacklist_ext = ["sh", "@SynoRessource"]

today = datetime.date.today()
treshold_date = today - datetime.timedelta(days=5)
year = str(treshold_date.year)
month = month_to_dir[treshold_date.month]

date_regex = r"^[\w\s_\-]*(?P<date>\d{2}\-\d{2}\-\d{4})\.pdf$"

transfer_from_root = "/volume2/Hausaufgaben/HAs"
transfer_to_root = "/volume2/Hausaufgaben/Archive"


class InvalidFormattingException(Exception):
    pass


class IsCompressedFileException(Exception):
    pass


class ArchiveManager:
    def __init__(self, debug=False):
        self.logger = fileloghelper.Logger(
            "/volume2/administration/auto_archive_files.log")
        self.transferred_files = []
        self.not_transferred_files = []
        self.debug = debug
        try:
            self.email_address = os.environ.get("EMAIL_ADDRESS")
            self.smtp = yagmail.SMTP(self.email_address,
                                     os.environ.get("EMAIL_PASSWD"))
        except TypeError:  # running tests
            self.email_address = ""
            self.smtp = None

    def parse_filename(self, fname: str):
        date = None
        f = os.path.split(fname)[1]
        try:
            groups = re.match(date_regex, f).groupdict()
            date = groups.get("date", None)
        except AttributeError:
            pass
        try:
            abbr = f.split(" ")[0]
            s = abbr_to_subject[abbr]
        except KeyError:
            raise InvalidFormattingException()
        if date is not None:
            d = datetime.datetime.strptime(date, "%d-%m-%Y")
            return (s, str(d.year), month_to_dir[d.month])
        return (s, None, None)

    def get_destination_for_file(self, filename: str):
        def return_timestamped_filepath():
            dest = os.path.join(transfer_to_root, s, y, m)
            if not os.path.isdir(dest):
                os.makedirs(dest)
            return os.path.join(dest, os.path.split(filename)[-1])
        try:
            # subject, year, month
            s, y, m = self.parse_filename(filename)
            if y is None or m is None:
                dest = filename
                if filename.startswith("/volume2/Hausaufgaben/HAs"):
                    y = year
                    m = month
                    return return_timestamped_filepath()
                # Put files that were in the wrong subject folder in the same
                # substructure (e.g. /Subject/2020) but for another subject
                for subject in abbr_to_subject.values():
                    dest = dest.replace(subject, s)
                return dest
            else:
                return return_timestamped_filepath()
        except (InvalidFormattingException, TypeError):
            self.logger.warning(f"Error parsing {filename}", False)
            return None

    def transfer_file(self, fname: str):
        """Might throw InvalidFormattingException or \
                IsCompressedFileException"""
        if fname.endswith(".small.pdf"):
            raise IsCompressedFileException()
        try:
            s, y, m = self.parse_filename(fname)
            if y is None:
                y = year
            if m is None:
                m = month
            destination = self.get_destination_for_file(fname)
            if destination == fname:
                return
            dest_dir = os.path.split(destination)[-1]
            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir)
            self.logger.debug(
                f"Trying to move {fname} to {destination}", self.debug)
            os.rename(fname, destination)
            self.logger.success(
                f"Transferred file from {fname} to {destination}", True)
            small_f = os.path.join(transfer_from_root,
                                   fname.replace(".pdf", ".small.pdf"))
            if os.path.isfile(small_f):
                os.remove(small_f)
                self.logger.debug(f"Deleted {small_f}")
            self.transferred_files.append(fname)
        except KeyError:
            self.not_transferred_files.append(fname)
            raise InvalidFormattingException()
        except InvalidFormattingException as e:
            self.not_transferred_files.append(fname)
            raise e

    def transfer_directory(self, path: str):
        self.logger.context = "archiving"
        self.logger.debug(f"Transferring/Archiving {path}", self.debug)
        for f in os.listdir(path):
            filepath = os.path.join(path, f)
            ext = f.split(".")[-1]
            if (ext not in blacklist_ext) and (not f.startswith("@"))\
                    and (f not in blacklist_files):
                try:
                    if os.path.isdir(filepath):
                        self.transfer_directory(filepath)
                    else:
                        self.transfer_file(filepath)
                except InvalidFormattingException:
                    self.logger.error(f"Invalid formatting on {f}")
                except IsCompressedFileException:
                    self.logger.warning(f"Is compressed file: {f}", False)
                except Exception as e:
                    self.logger.error(
                        f"Error occured when transferring {f}.")
                    self.logger.handle_exception(e)

    def transfer_all_files(self):
        self.logger.context = "mail"
        self.transfer_directory(transfer_from_root)
        mail_body = ["The following files were successfully archived: "]\
            + self.transferred_files
        if len(self.not_transferred_files) > 0:
            mail_body += ["", f"Also, these files ({len(self.not_transferred_files)})\
                    were not archived:"]
            mail_body += self.not_transferred_files
        mail_body.append(f"Thats {len(self.transferred_files)} files.")
        mail_subject = "[NAS] Archiving at end of week"
        self.smtp.send(self.email_address, mail_subject, mail_body)
        self.logger.success("Sent mail notifying of the archiving process.")

    def reorganize_all_files(self, directory: str = transfer_to_root):
        """For every file, use `transfer_file` to reorganize it."""
        self.logger.context = "reorganization"
        self.logger.debug(f"Reorganizing {directory}")
        for root, dirs, files in os.walk(directory):
            for f in files:
                blacklist = False
                for ext in blacklist_ext:
                    if f.endswith(ext):
                        blacklist = True
                if f in blacklist_files or blacklist:
                    continue
                try:
                    self.transfer_file(os.path.join(root, f))
                except (InvalidFormattingException, TypeError):
                    self.logger.warning(f"Error parsing {f}", False)
                except FileNotFoundError as e:
                    self.logger.error(f"File not found: {e}")
        if directory == transfer_to_root:
            self.logger.info(
                f"Transferred {len(self.transferred_files)} files:", True)
            [self.logger.debug(f, self.debug) for f in self.transferred_files]


def main():
    manager = ArchiveManager()
    manager.logger.header(True, True)
    parser = argparse.ArgumentParser(
        description="Archive files from HAs or reorganize Archive.")
    parser.add_argument("action", type=str,
                        help="Action to perform (archive, reorganize)")
    parser.add_argument("--debug", "-d", action="store_true",
                        help="debug mode (additional logging)")
    args = parser.parse_args()
    manager.debug = args.debug
    manager.logger.autosave = manager.debug
    if args.action == "archive":
        manager.transfer_all_files()
    elif args.action == "reorganize":
        manager.reorganize_all_files()
    else:
        parser.print_help()
    manager.logger.save()


if __name__ == "__main__":
    main()
