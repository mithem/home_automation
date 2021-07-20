"""HomeAutomation: a collection of scripts and small programs automating primarily homework on NAS and some small helpers for day-to-day life."""
import argparse
import datetime
import os
import re

import fileloghelper
import yagmail

from home_automation import config

MONTH_TO_DIR = {
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

ABBR_TO_SUBJECT = {
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

BLACKLIST_FILES = [".DS_Store", "@eaDir"]
BLACKLIST_EXT = ["sh", "@SynoRessource"]

TODAY = datetime.date.today()
TRESHOLD_DATE = TODAY - datetime.timedelta(days=5)
YEAR = str(TRESHOLD_DATE.year)
MONTH = MONTH_TO_DIR[TRESHOLD_DATE.month]

DATE_REGEX = r"^[\w\s_\-]*(KW((?P<calendar_week>\d{1,2}))|" \
             + r"(?P<date>(\d{2}\-\d{2}\-\d{4})|(\d{4}\-\d{2}\-\d{2})))[\w\s_\-]*\.pdf$"

TRANSFER_FROM_ROOT = "/volume2/Hausaufgaben/HAs"
TRANSFER_TO_ROOT = "/volume2/Hausaufgaben/Archive"


class InvalidFormattingException(Exception):
    """An exception thrown when a file is invalidly formatted."""


class IsCompressedFileException(Exception):
    """An exception thrown when a file is already compressed."""


class ArchiveManager:
    """ArchiveManager managed the archive."""

    def __init__(self, debug=False):
        self.logger = fileloghelper.Logger(os.path.join(
            os.environ.get("LOG_DIR"), "ArchiveManager.log"), autosave=debug)
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

    def parse_filename(self, path: str):  # pylint: disable=no-self-use
        """parse filename and return (subject, year, month), each as the name of the directory the file is supposed to go in."""
        date_str = None
        calendar_week = None
        fname = os.path.split(path)[1]
        match = re.match(DATE_REGEX, fname)
        if match:
            groups = match.groupdict()
            date_str = groups.get("date", None)
            calendar_week = groups.get("calendar_week", None)
        try:
            abbr = fname.split(" ")[0]
            subject = ABBR_TO_SUBJECT[abbr]
        except (KeyError, IndexError) as error:
            raise InvalidFormattingException(path) from error
        try:
            if date_str:
                try:
                    date = datetime.datetime.strptime(date_str, "%d-%m-%Y")
                except ValueError:
                    date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                return (subject, str(date.year), MONTH_TO_DIR[date.month])
            if calendar_week is not None:
                # https://stackoverflow.com/questions/17087314/get-date-from-week-number,
                # using isoweeks
                date = datetime.datetime.strptime(
                    f"{TODAY.year}-W{calendar_week.zfill(2)}-1", "%G-W%V-%u")
                return (subject, str(date.year), MONTH_TO_DIR[date.month])
        except ValueError as error:
            raise InvalidFormattingException(path) from error
        return (subject, None, None)

    def get_destination_for_file(self, filename: str):
        """Get appropriate destination for file (got that guess right?!?!).
        Might throw InvalidFormattingException."""
        def return_timestamped_filepath():
            dest = os.path.join(TRANSFER_TO_ROOT, subject, year, month)
            if not os.path.isdir(dest):
                os.makedirs(dest)
            return os.path.join(dest, os.path.split(filename)[-1])
        try:
            subject, year, month = self.parse_filename(filename)
            if year is None or month is None:
                dest = filename
                if filename.startswith("/volume2/Hausaufgaben/HAs"):
                    year = YEAR
                    month = MONTH
                    return return_timestamped_filepath()
                # Put files that were in the wrong subject folder in the same
                # substructure (e.g. /Subject/2020) but for another subject
                for sub in ABBR_TO_SUBJECT.values():
                    dest = dest.replace(sub, subject)
                return dest
            return return_timestamped_filepath()
        except (InvalidFormattingException, TypeError) as error:
            self.logger.warning(f"Error parsing {filename}", False)
            raise InvalidFormattingException(filename) from error

    def transfer_file(self, fname: str):
        """Transfer file in corresponding, correct (worked out in this method) spot.
        Might also not be a file but directory instead, which will then also be
        transferred as a whole in the archive.
        Might throw InvalidFormattingException or
        IsCompressedFileException"""
        if fname.endswith(".small.pdf"):
            raise IsCompressedFileException()
        try:
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
            small_f = os.path.join(TRANSFER_FROM_ROOT,
                                   fname.replace(".pdf", ".small.pdf"))
            if os.path.isfile(small_f):
                os.remove(small_f)
                self.logger.debug(f"Deleted {small_f}")
            self.transferred_files.append(fname)
        except InvalidFormattingException as error:
            self.not_transferred_files.append(fname)
            raise error

    def transfer_directory(self, path: str):
        """Transfer all files and directories in given directory."""
        def handle_file(filepath):
            try:
                if os.path.isdir(filepath):
                    did_move_invalidly_formatted_directory = False
                    # ...with validly formatted files
                    subject = None
                    try:
                        subject, _, _ = self.parse_filename(filepath)
                    except InvalidFormattingException:
                        did_move_invalidly_formatted_directory = True
                    if subject is not None:
                        self.transfer_file(filepath)
                    else:
                        self.transfer_directory(filepath)
                        if did_move_invalidly_formatted_directory:
                            os.removedirs(filepath)
                else:
                    self.transfer_file(filepath)
            except InvalidFormattingException:
                self.logger.error(f"Invalid formatting on {filepath}")
            except IsCompressedFileException:
                self.logger.warning(f"Is compressed file: {filepath}", False)
            except Exception as error:  # pylint: disable=broad-except
                # better safe than sorry
                self.logger.error(
                    f"Error occured when transferring {filepath}.")
                self.logger.handle_exception(error)
        self.logger.context = "archiving"
        self.logger.debug(f"Transferring/Archiving {path}", self.debug)
        for fname in os.listdir(path):
            filepath = os.path.join(path, fname)
            ext = fname.split(".")[-1]
            if (ext not in BLACKLIST_EXT) and (not fname.startswith("@"))\
                    and (fname not in BLACKLIST_FILES):
                handle_file(filepath)

    def transfer_all_files(self):
        """Transfer all files from the root directory (not necessarily '/') to their corresponding destination."""
        self.logger.context = "mail"
        self.transfer_directory(TRANSFER_FROM_ROOT)
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

    def reorganize_all_files(self):
        """For every file, use `transfer_file` to reorganize it."""
        self.logger.context = "reorganization"
        self.logger.debug("Reorganizing!")
        self.transfer_directory(TRANSFER_TO_ROOT)
        self.logger.info(
            f"Transferred {len(self.transferred_files)} files:", True)
        for fname in self.transferred_files:
            self.logger.debug(
                fname, self.debug)  # pylint: disable=multiple-statements
        # I mean, common!


def main():
    """Guess what this does, pylint!"""
    manager = ArchiveManager()
    manager.logger.header(True, True)
    parser = argparse.ArgumentParser(
        description="Archive files from HAs or reorganize Archive.")
    parser.add_argument("action", type=str,
                        help="Action to perform (archive, reorganize)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="verbose mode (additional logging (to stdout))")
    args = parser.parse_args()
    manager.debug = args.verbose
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
