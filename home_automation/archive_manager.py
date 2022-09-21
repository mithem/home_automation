"""HomeAutomation: a collection of scripts and small programs automating
primarily homework on NAS and some small helpers for day-to-day life."""
import argparse
import datetime
import os
import re
import shutil
from typing import List, Sequence, Optional

import fileloghelper
import home_automation.utilities
import home_automation.server.backend.state_manager
from home_automation.server.backend import oauth2_helpers
from home_automation import config as haconfig
from home_automation.constants import MONTH_TO_DIR, ABBR_TO_SUBJECT

BLACKLIST_FILES = [".DS_Store", "@eaDir"]
BLACKLIST_EXT = ["sh", "@SynoRessource"]

TODAY = datetime.date.today()
TRESHOLD_DATE = TODAY - datetime.timedelta(days=5)
YEAR = str(TRESHOLD_DATE.year)
MONTH = MONTH_TO_DIR[TRESHOLD_DATE.month]

DATE_REGEX = (
    r"^[\w\s_\-]*(KW((?P<calendar_week>\d{1,2}))|"
    + r"(?P<date>(\d{2}\-\d{2}\-\d{4})|(\d{4}\-\d{2}\-\d{2})))[\w\s_\-]*\.pdf$"
)
YEAR_REGEX = r"^.+(?P<year>\d\d\d\d).+$"
NO_TRANSFER_REGEX = r"^.*(?P<notransferflag>NO(_|-)?TRANSFER).*$"


class InvalidFormattingException(Exception):
    """An exception thrown when a file is invalidly formatted."""


class IsCompressedFileException(Exception):
    """An exception thrown when a file is already compressed."""


class ArchiveManager:  # pylint: disable=too-many-instance-attributes
    """ArchiveManager manages the archive. Wait, what?"""

    config: haconfig.Config
    logger: fileloghelper.Logger
    transferred_files: List[str]
    not_transferred_files: List[str]
    debug: bool

    def __init__(self, config: haconfig.Config, debug=False):
        self.config = config
        self.logger = fileloghelper.Logger(
            os.path.join(config.log_dir, "archive_manager.log"), autosave=debug
        )
        self.transferred_files = []
        self.not_transferred_files = []
        self.debug = debug

    @staticmethod
    def parse_filename(path: str):
        """parse filename and return (subject, year, month), each as
        the name of the directory the file is supposed to go in."""
        date_str = None
        calendar_week = None
        year_str = None
        fname = os.path.split(path)[1]
        date_match = re.match(DATE_REGEX, fname)
        year_match = re.match(YEAR_REGEX, path)
        if date_match:
            groups = date_match.groupdict()
            date_str = groups.get("date", None)
            calendar_week = groups.get("calendar_week", None)
        if year_match:
            groups = year_match.groupdict()
            year_str = groups.get("year", "")
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
                year = year_str if year_str else TODAY.year
                date = datetime.datetime.strptime(
                    f"{year}-W{calendar_week.zfill(2)}-1", "%G-W%V-%u"
                )
                return (subject, str(date.year), MONTH_TO_DIR[date.month])
        except ValueError as error:
            raise InvalidFormattingException(path) from error
        return (subject, None, None)

    def get_destination_for_file(self, path: str):
        """Get appropriate destination for file (got that guess right?!?!).
        Might throw InvalidFormattingException."""

        def return_timestamped_filepath():
            dest = os.path.join(self.config.archive_dir, subject, year, month)
            if not os.path.isdir(dest):
                os.makedirs(dest)
            return os.path.join(dest, os.path.split(path)[-1])

        try:
            no_transfer_match = re.match(NO_TRANSFER_REGEX, path, re.IGNORECASE)
            if no_transfer_match:
                return path
            subject, year, month = ArchiveManager.parse_filename(path)
            if year is None or month is None:
                # e.g. is in Archive/Physik/2021/Juni or lower
                a_dir = (
                    self.config.archive_dir
                    if not self.config.archive_dir.endswith("/")
                    else self.config.archive_dir[:-1]
                )
                is_in_lowest_level_archive = (
                    os.path.split(
                        os.path.split(os.path.split(os.path.split(path)[0])[0])[0]
                    )[0]
                    == a_dir
                )  # better way to do this?
                if (
                    path.startswith(self.config.homework_dir)
                    or not is_in_lowest_level_archive
                ):
                    year = YEAR
                    month = MONTH
                    return return_timestamped_filepath()
                # Put files that were in the wrong subject folder in the same
                # substructure (e.g. /Subject/2020) but for another subject
                for sub in ABBR_TO_SUBJECT.values():
                    path = path.replace(sub, subject)
                return path
            return return_timestamped_filepath()
        except (InvalidFormattingException, TypeError) as error:
            self.logger.warning(f"Error parsing '{path}'", False)
            raise InvalidFormattingException(path) from error

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
                f"Trying to move '{fname}' to '{destination}'", self.debug
            )
            shutil.move(fname, destination)
            self.logger.success(
                f"Transferred file from '{fname}' to '{destination}'", True
            )
            small_f = os.path.join(
                self.config.homework_dir, fname.replace(".pdf", ".small.pdf")
            )
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
                        subject, _, _ = ArchiveManager.parse_filename(filepath)
                    except InvalidFormattingException:
                        did_move_invalidly_formatted_directory = True
                    if subject is not None:
                        self.transfer_file(filepath)
                    else:
                        self.transfer_directory(filepath)
                        if (
                            did_move_invalidly_formatted_directory
                            and os.path.split(filepath)[0] == self.config.homework_dir
                        ):
                            os.removedirs(filepath)
                else:
                    self.transfer_file(filepath)
            except InvalidFormattingException:
                self.logger.error(f"Invalid formatting on {filepath}")
            except IsCompressedFileException:
                self.logger.warning(f"Is compressed file: {filepath}", False)
            except Exception as error:  # pylint: disable=broad-except
                # better safe than sorry
                self.logger.error(f"Error occured when transferring {filepath}.")
                self.logger.handle_exception(error)

        self.logger.context = "archiving"
        self.logger.debug(f"Transferring/Archiving {path}", self.debug)
        for fname in os.listdir(path):
            filepath = os.path.join(path, fname)
            ext = fname.split(".")[-1]
            if (
                (ext not in BLACKLIST_EXT)
                and (not fname.startswith("@"))
                and (fname not in BLACKLIST_FILES)
            ):
                handle_file(filepath)

    def transfer_all_files(self):
        """Transfer all files from the root directory (not
        necessarily '/') to their corresponding destination."""
        self.logger.context = "mail"
        self.transfer_directory(self.config.homework_dir)
        self.send_archiving_mail()

    def send_archiving_mail(self):
        """Send mail to notify that the archiving process has finished."""
        if len(self.transferred_files) == 0 and len(self.not_transferred_files) == 0:
            self.logger.info("No files transferred or failed to be transferred.")
            return
        mail_body = "The following files were successfully archived:\n" + "\n".join(
            self.transferred_files
        )
        if len(self.not_transferred_files) > 0:
            mail_body += f"\nAlso, these files \
({len(self.not_transferred_files)}) were not archived:\n"
            mail_body += "\n".join(self.not_transferred_files)
        mail_body += f"\nThat's {len(self.transferred_files)} files."
        mail_subject = "[NAS] Archiving at end of week"
        state_manager = home_automation.server.backend.state_manager.StateManager(
            self.config.db_path
        )
        creds = oauth2_helpers.get_google_oauth2_credentials(state_manager)
        home_automation.utilities.send_mail(creds, mail_subject, mail_body)
        self.logger.success("Sent mail notifying of the archiving process.")

    def reorganize_all_files(self):
        """For every file, use `transfer_file` to reorganize it."""
        self.logger.context = "reorganization"
        self.logger.debug("Reorganizing!")
        self.transfer_directory(self.config.archive_dir)
        self.logger.info(f"Transferred {len(self.transferred_files)} files:", True)
        for fname in self.transferred_files:
            self.logger.debug(fname, self.debug)  # pylint: disable=multiple-statements
        # I mean, common!


def archive():
    """Archive with the default config loaded (still from filesystem)"""
    config_data = haconfig.load_config()
    manager = ArchiveManager(config_data)
    manager.transfer_all_files()


def reorganize():
    """Reorganize with the default config loaded (still from filesystem)"""
    config_data = haconfig.load_config()
    manager = ArchiveManager(config_data)
    manager.reorganize_all_files()


def main(arguments: Optional[Sequence[str]] = None):
    """Guess what this does, pylint!"""
    parser = argparse.ArgumentParser(
        description="Archive files from HAs or reorganize Archive."
    )
    parser.add_argument(
        "action", type=str, help="Action to perform (archive, reorganize)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="verbose mode (additional logging (to stdout))",
    )
    parser = home_automation.utilities.argparse_add_argument_for_config_file_path(
        parser
    )
    args = parser.parse_args(arguments)
    config_data = haconfig.load_config(path=args.config)
    manager = ArchiveManager(config_data, args.verbose)
    manager.logger.header(True, True)
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
