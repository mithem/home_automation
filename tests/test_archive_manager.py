import datetime
import os
from typing import Dict, Optional

import pytest
from pyfakefs.fake_filesystem_unittest import TestCase
from test_config import VALID_CONFIG
from home_automation.archive_manager import (ABBR_TO_SUBJECT, BLACKLIST_EXT,
                                             BLACKLIST_FILES, MONTH_TO_DIR,
                                             TRESHOLD_DATE, ArchiveManager,
                                             InvalidFormattingException,
                                             IsCompressedFileException)
from home_automation import config

_NOW = datetime.datetime.now()
CURRENT_YEAR = str(_NOW.year)


class AnyTestCase(TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        config.load_into_environment(config.parse_config(VALID_CONFIG))
        self.manager = ArchiveManager(debug=True)
        self.useful_data = {
            "year": str(TRESHOLD_DATE.year),
            "month": MONTH_TO_DIR[TRESHOLD_DATE.month]
        }


class TestParseFilename(AnyTestCase):

    def evaluate(self, f, s, y, m):
        _s, _y, _m = self.manager.parse_filename(f)
        assert _s == ABBR_TO_SUBJECT[s] and _y == str(
            y) and _m == MONTH_TO_DIR[m]

    def year_and_month_for_calendar_week(self, week):
        # https://stackoverflow.com/questions/17087314/get-date-from-week-number,
        # using iso weeks
        date_str = CURRENT_YEAR + "-W" + str(week).zfill(2) + "-1"
        d = datetime.datetime.strptime(date_str, "%G-W%V-%u")
        return (d.year, d.month)

    def test_parse_filename_standard_formatting(self):
        self.evaluate("/volume2/PH HA 22-06-2021.pdf", "PH", 2021, 6)
        self.evaluate("/volume2/PH HA 01-12-2021.pdf", "PH", 2021, 12)

    def test_parse_filename_calendar_weeks(self):
        y, m = self.year_and_month_for_calendar_week(7)
        self.evaluate("/volume2/PH HA KW7.pdf", "PH", y, m)
        y, m = self.year_and_month_for_calendar_week(1)
        self.evaluate("/volume2/PH HA KW01.pdf", "PH", y, m)
        y, m = self.year_and_month_for_calendar_week(50)
        self.evaluate("/volume2/PH HA KW50.pdf", "PH", y, m)

    def test_parse_filename_iso_formatting(self):
        self.evaluate("/volume2/PH HA 2021-06-22.pdf", "PH", 2021, 6)
        self.evaluate("/volume2/PH HA 2021-12-01.pdf", "PH", 2021, 12)

    def test_parse_filename_partial_formatting(self):
        s, y, m = self.manager.parse_filename(
            "/volume1/PH Klausurvorbereitung.pdf")

        assert s == ABBR_TO_SUBJECT["PH"]
        assert y is None
        assert m is None

    def test_parse_filename_raises_invalid_formatting_exception(self):
        with pytest.raises(InvalidFormattingException):
            _ = self.manager.parse_filename("/volume1/test.pdf")

        with pytest.raises(InvalidFormattingException):
            _ = self.manager.parse_filename("/volume2/PH KW55.pdf")

        with pytest.raises(InvalidFormattingException):
            _ = self.manager.parse_filename(
                "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/test.pdf")


class TestGetDestinationForFile(AnyTestCase):
    def test_get_destination_for_file_same_origin_and_destination(self):
        s = "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/"\
            + "PH HA 22-06-2021.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest == s

    def test_get_destination_for_file_file_not_in_lowest_level_structure(self):
        s = "/volume2/Hausaufgaben/Archive/Physik/2021/PH HA 22-06-2021.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest == s.replace("/2021/", "/2021/" + MONTH_TO_DIR[6] + "/")

    def test_get_destination_for_file_raises_invalid_formatting_exception(self):
        s = "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/test.pdf"

        with pytest.raises(InvalidFormattingException):
            _ = self.manager.get_destination_for_file(s)

    def test_get_destination_for_file_file_in_correct_substructure_but_wrong_subject_directory(self):
        s = "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/"\
            + "M HA 22-06-2021.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest == s.replace("Physik", "Mathe")

    def test_get_destination_for_file_messed_up_archive(self):
        # yup, something similar happened 😅
        s = "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/Physik/2021/Juni/"\
            + "2021/Juni/Physik/Juni/2021/PH HA 22-06-2021.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest == "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/"\
            + "PH HA 22-06-2021.pdf"

    def test_get_destination_for_file_messed_up_archive_2(self):
        s = "/volume2/Hausaufgaben/Archive/PH HA 22-06-2021.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest == "/volume2/Hausaufgaben/Archive/"\
            + ABBR_TO_SUBJECT["PH"] + "/2021/" + \
            MONTH_TO_DIR[6] + "/PH HA 22-06-2021.pdf"

    def test_get_destination_for_file_messed_up_archive_3(self):
        s = "/volume2/Hausaufgaben/Archive/Mathe/2021/Juni/PH KW25.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest == s.replace("Mathe", "Physik")

    def test_get_destination_for_file_from_HAs_date_parsable(self):
        s = "/volume2/Hausaufgaben/HAs/PH HA 22-06-2021.pdf"
        expected = "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/"\
            + "PH HA 22-06-2021.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest == expected

    def test_get_destination_for_file_from_HAs_date_not_parsable(self):
        s = "/volume2/Hausaufgaben/HAs/PH Klausurvorbereitung.pdf"
        expected = "/volume2/Hausaufgaben/Archive/Physik/"\
            + self.useful_data['year'] + "/"\
            + self.useful_data['month']\
            + "/PH Klausurvorbereitung.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest == expected

    def test_get_destination_for_file_from_somewhere_in_archive_date_not_parsable(self):
        s = "/volume2/Hausaufgaben/Archive/Physik/PH HA.pdf"
        expected = "/volume2/Hausaufgaben/Archive/Physik/"\
            + self.useful_data["year"] + "/"\
            + self.useful_data["month"]\
            + "/PH HA.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest == expected

    def test_get_destination_for_file_in_lowlevel_archive_date_not_parsable(self):
        s = "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/PH HA.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest == s


class TestTransferFile(AnyTestCase):
    def test_transfer_file_throws_is_compressed_file_exception(self):
        s = "/volume2/Hausaufgaben/HAs/test.small.pdf"

        with pytest.raises(IsCompressedFileException):
            self.manager.transfer_file(s)

        # no spam in email stating a thousand compressed files were not
        # transferred
        assert self.manager.not_transferred_files == []
        assert self.manager.transferred_files == []

    def test_transfer_file_throws_is_compressed_file_exception_2(self):
        s = "/volume2/Hausaufgaben/HAs/PH HA 22-06-2021.small.pdf"

        with pytest.raises(IsCompressedFileException):
            self.manager.transfer_file(s)

        # no spam in email stating a thousand compressed files were not
        # transferred
        assert self.manager.not_transferred_files == []
        assert self.manager.transferred_files == []

    def test_transfer_file_throws_invalid_formatting_exception(self):
        s = "/volume2/Hausaufgaben/HAs/test.pdf"

        with pytest.raises(InvalidFormattingException):
            self.manager.transfer_file(s)

        assert self.manager.transferred_files == []
        assert self.manager.not_transferred_files == [s]

    def test_transfer_file_from_HAs(self):
        s = "/volume2/Hausaufgaben/HAs/PH HA 22-06-2021.pdf"
        expected = "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/"\
            + "PH HA 22-06-2021.pdf"
        self.fs.create_file(s)

        self.manager.transfer_file(s)

        assert not self.fs.exists(s)
        assert self.fs.exists(expected)
        assert self.manager.transferred_files == [s]
        assert self.manager.not_transferred_files == []

    def test_transfer_file_from_HAs_deletes_small_pdf(self):
        s1 = "/volume2/Hausaufgaben/HAs/PH HA 22-06-2021.pdf"
        s2 = s1.replace(".pdf", ".small.pdf")
        # only check if .small.pdf is deleted as the rest is already tested for
        # in `test_transfer_file_from_HAs`
        self.fs.create_file(s1)
        self.fs.create_file(s2)

        self.manager.transfer_file(s1)

        assert not self.fs.exists(s1)
        assert not self.fs.exists(s2)
        assert self.manager.transferred_files == [s1]
        assert self.manager.not_transferred_files == []

    def test_transfer_file_from_Archive(self):
        s = "/volume2/Hausaufgaben/Archive/Physik/PH HA 22-06-2021.pdf"
        expected = s.replace("Physik", "Physik/2021/Juni")
        self.fs.create_file(s)

        self.manager.transfer_file(s)

        assert not self.fs.exists(s)
        assert self.fs.exists(expected)
        assert self.manager.transferred_files == [s]
        assert self.manager.not_transferred_files == []

    def test_transfer_file_same_origin_and_destination(self):
        files = [
            "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/PH HA 22-06-2021.pdf",
            "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/PH HA.pdf",
        ]
        for path in files:
            self.fs.create_file(path)
            self.manager.transfer_file(path)
            assert self.fs.exists(path)
            for line in self.manager.logger._lines:
                assert not f"Transferred file from {path} to {path}" in line

        assert self.manager.transferred_files == []
        assert self.manager.not_transferred_files == []

    def test_transfer_file_uhm_actually_its_a_dir(self):
        root = "/volume2/Hausaufgaben/HAs/PH KW25"
        f_list = ["text1.md", "script.py", "PH HA.pdf", "PH HA 22-06-2021.pdf"]
        self.fs.create_dir(root)
        for f in f_list:
            self.fs.create_file(os.path.join(root, f))

        self.manager.transfer_file(root)

        new_root = "/volume2/Hausaufgaben/Archive/Physik/" + \
            str(self.useful_data["year"]) + "/" + \
            self.useful_data["month"] + "/PH KW25/"
        assert not self.fs.exists(root)
        assert self.fs.exists(new_root)
        for f in f_list:
            assert self.fs.exists(os.path.join(new_root, f))

    def test_transfer_file_uhm_actually_its_a_dir_2(self):
        root = "/volume2/Hausaufgaben/HAs/PH Material"
        f_list = ["text1.md", "script.py", "PH HA.pdf", "PH HA 22-06-2021.pdf"]
        self.fs.create_dir(root)
        for f in f_list:
            self.fs.create_file(os.path.join(root, f))

        self.manager.transfer_file(root)

        new_root = "/volume2/Hausaufgaben/Archive/Physik/" + \
            str(self.useful_data["year"]) + "/" + \
            self.useful_data["month"] + "/PH Material/"
        assert not self.fs.exists(root)
        assert self.fs.exists(new_root)
        for f in f_list:
            assert self.fs.exists(os.path.join(new_root, f))

    def test_transfer_file_uses_correct_homework_and_archive_root(self):
        override_env = {
            "HOMEWORK_DIR": "/var/school/homework",
            "ARCHIVE_DIR": "/var/school/archive"
        }
        for key, value in override_env.items():
            os.environ[key] = value
        subject = list(ABBR_TO_SUBJECT.keys())[0].upper()
        fname = subject + " HA 22-06-2021.pdf"
        path = os.path.join(override_env["HOMEWORK_DIR"], fname)
        dest = os.path.join(
            override_env["ARCHIVE_DIR"],
            ABBR_TO_SUBJECT[subject],
            "2021",
            MONTH_TO_DIR[6],
            fname
        )

        self.fs.create_file(path)
        # needs to load environment variables and that good that way
        # (anything else would make debugging in a changing environment a nightmare)
        manager = ArchiveManager(True)

        manager.transfer_file(path)

        assert self.fs.exists(dest)
        assert not self.fs.exists(path)
        assert manager.transferred_files == [path]
        assert manager.not_transferred_files == []

    def test_transfer_file_creates_directories(self):
        s = "/volume2/Hausaufgaben/Archive/PH HA 22-06-2021.pdf"
        self.fs.create_file(s)
        assert len(os.listdir("/volume2/Hausaufgaben/Archive")) == 1

        self.manager.transfer_file(s)

        assert not self.fs.exists(s)
        assert self.fs.exists(
            "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/PH HA 22-06-2021.pdf")
        assert self.manager.transferred_files == [s]
        assert self.manager.not_transferred_files == []


class TestTransferDirectory(AnyTestCase):

    def test_transfer_directory(self):
        def f(name: str) -> str:
            return "/volume2/Hausaufgaben/Archive/" + name
        s1 = f("Physik/PH HA 22-06-2021.pdf")
        s2 = f("Physik/PH HA 22-05-2021.pdf")
        s3 = f("Physik/M HA 22-06-2021.pdf")
        s4 = f("Physik/PH HA 22-06-2021.small.pdf")
        s5 = f("Physik/test.pdf")
        self.fs.create_file(s1)
        self.fs.create_file(s2)
        self.fs.create_file(s3)
        self.fs.create_file(s4)
        self.fs.create_file(s5)

        self.manager.transfer_directory(f("Physik"))

        assert self.fs.exists(f("Physik/2021/Juni/PH HA 22-06-2021.pdf"))
        assert self.fs.exists(f("Physik/2021/Mai/PH HA 22-05-2021.pdf"))
        assert self.fs.exists(f("Mathe/2021/Juni/M HA 22-06-2021.pdf"))
        assert self.fs.exists(f("Physik/test.pdf"))

        assert not self.fs.exists(f("Physik/PH HA 22-06-2021.small.pdf"))
        assert not self.fs.exists(f("Physik/PH HA 22-06-2021.pdf"))
        assert not self.fs.exists(f("Physik/PH HA 22-05-2021.pdf"))
        assert not self.fs.exists(f("Physik/M HA 22-06-2021.pdf"))

        assert self.manager.transferred_files == [s1, s2, s3]
        assert self.manager.not_transferred_files == [s5]

    def test_transfer_directory_with_folder_valid_formatting(self):
        def f1(name: str) -> str:
            return "/volume2/Hausaufgaben/HAs"\
                + ("/" if len(name) > 0 else "")\
                + name

        def f2(name: str) -> str:
            return "/volume2/Hausaufgaben/Archive/" + ABBR_TO_SUBJECT['PH'] \
                + "/"\
                + self.useful_data['year']\
                + "/"\
                + self.useful_data['month']\
                + "/PH KW25/" + name
        dir_files = ["PH run.py", "PH lib.py"]
        self.fs.create_dir(f1(""))
        for fname in dir_files:
            self.fs.create_file(f1("PH KW25/") + fname)

        self.manager.transfer_directory(f1(""))

        for fname in dir_files:
            assert self.fs.exists(f2(fname))

        assert not self.fs.exists(f1("PH KW"))

        assert self.manager.transferred_files == [f1("PH KW25")]
        assert self.manager.not_transferred_files == []

    def test_transfer_directory_with_folder_invalid_formatting_files_valid(self):
        def f1(name: str) -> str:
            return "/volume2/Hausaufgaben/HAs"\
                + ("/" if len(name) > 0 else "")\
                + name

        def f2(name: str) -> str:
            return "/volume2/Hausaufgaben/Archive/"\
                + ABBR_TO_SUBJECT['PH'] \
                + "/2021/Juni/" \
                + name

        dir_files = ["PH HA 22-06-2021.pdf", "PH HA 23-06-2021.pdf"]
        self.fs.create_dir(f1(""))

        for fname in dir_files:
            self.fs.create_file(f1("Material/") + fname)

        self.manager.transfer_directory(f1(""))

        for fname in dir_files:
            assert self.fs.exists(f2(fname))

        assert not self.fs.exists(f1("Material"))
        for fname in dir_files:
            assert f1("Material/" + fname) in self.manager.transferred_files
        assert len(self.manager.transferred_files) == len(dir_files)
        assert self.manager.not_transferred_files == []

    def test_transfer_directory_with_folder_invalid_formatting_files_invalid(self):
        def f1(name: str) -> str:
            return "/volume2/Hausaufgaben/HAs"\
                + ("/" if len(name) > 0 else "")\
                + name

        dir_files = ["lib.py", "main.py"]
        self.fs.create_dir(f1(""))

        for fname in dir_files:
            self.fs.create_file(f1("Scripts/") + fname)

        self.manager.transfer_directory(f1(""))

        assert self.fs.exists(f1("Scripts"))
        for fname in dir_files:
            assert self.fs.exists(f1("Scripts/") + fname)
            assert f1("Scripts/") + fname in self.manager.not_transferred_files
        assert len(self.manager.not_transferred_files) == len(dir_files)
        assert self.manager.transferred_files == []

    def test_transfer_directory_BLACKLIST_FILES(self):
        def f(name: str) -> str:
            return "/volume2/Hausaufgaben/HAs"\
                + ("/" if len(name) > 0 else "")\
                + name
        # not sure why i need to do that
        self.fs.create_dir("/volume2/Hausaufgaben/HAs")
        for fname in BLACKLIST_FILES:
            if len(fname.split(".")) > 0:
                self.fs.create_file(fname)
            else:
                self.fs.create_dir(fname)

        self.manager.transfer_directory(f(""))

        for fname in BLACKLIST_FILES:
            assert self.fs.exists(fname)

        assert self.manager.not_transferred_files == []
        assert self.manager.transferred_files == []

    def test_transfer_directory_BLACKLIST_EXT(self):
        def f(name: str) -> str:
            return "/volume2/Hausaufgaben/HAs"\
                + ("/" if len(name) > 0 else "")\
                + name
        self.fs.create_dir("/volume2/Hausaufgaben/HAs")
        for ext in BLACKLIST_EXT:
            self.fs.create_file("hello" + ext)

        self.manager.transfer_directory(f(""))

        for ext in BLACKLIST_EXT:
            assert self.fs.exists("hello" + ext)

        assert self.manager.transferred_files == []
        assert self.manager.not_transferred_files == []


class TestReorganizeAllFiles(AnyTestCase):
    def setup_root_directory_with_files(self, structure):
        """Use `structure` to create files in directory above HOMEWORK_DIR & ARCHIVE_DIR.
        Example:
        ```python
        {"HAs": {
            "PH Material": {
                "text1.pdf": None,
                "text2.pdf": None
            },
            "PH HA 22-06-2021.pdf": None,
            "PH HA 23-06-2021.pdf": None
        }
        ```
        """
        def create_dir(directory: Dict[str, Optional[Dict]], path: str):
            for relative_path, value in directory.items():
                p = os.path.join(path, relative_path)
                if value:
                    self.fs.create_dir(p)
                    create_dir(value, p)
                else:
                    self.fs.create_file(p)

        create_dir(structure, "/volume2/Hausaufgaben")

    def evaluate_root_directory_with_files(self, structure):
        """The same as `setup_root_directory_with_files`, just the existance of the files is
        asserted (and that there aren't any other files in that directory)"""
        def check_dir(directory: Dict[str, Optional[Dict]], path: str):
            for relative_path, value in directory.items():
                p = os.path.join(path, relative_path)
                if value:
                    dirlist = os.listdir(p)
                    assert os.path.isdir(p)
                    assert sorted(dirlist) == sorted(value.keys())
                    check_dir(value, p)
                else:
                    assert self.fs.exists(p)

        check_dir(structure, "/volume2/Hausaufgaben")

    def test_setup_root_directory_with_files(self):
        """Yep, a test for a test!"""
        def f(name: str) -> str:
            return "/volume2/Hausaufgaben/" + name
        s1 = "test.pdf"
        s2 = "HAs/test2.pdf"
        s3 = "HAs/PH Material/text1.pdf"
        s4 = "Archive/test3.pdf"
        s5 = "Archive/Physik/2021/Juni/PH HA 22-06-2021.pdf"
        inp = {
            "test.pdf": None,
            "HAs": {
                "test2.pdf": None,
                "PH Material": {
                    "text1.pdf": None,
                }
            },
            "Archive": {
                "test3.pdf": None,
                "Physik": {
                    "2021": {
                        "Juni": {
                            "PH HA 22-06-2021.pdf": None
                        }
                    }
                }
            }
        }
        self.setup_root_directory_with_files(inp)

        assert self.fs.exists(f(s1))
        assert self.fs.exists(f(s2))
        assert self.fs.exists(f(s3))
        assert self.fs.exists(f(s4))
        assert self.fs.exists(f(s5))

    def test_reorganize_all_files(self):
        structure = {
            "HAs": {
                "test1.pdf": None,
                "test2.pdf": None,
                "PH Material": {
                    "text1.pdf": None,
                    "PH HA 22-06-2021.pdf": None,
                    "text2.pdf": None
                }
            },
            "Archive": {
                "something_lost.pdf": None,
                "Physik": {
                    "something_lost_2.pdf": None,
                    "PH HA 23-06-2021.pdf": None,
                    "PH HA.pdf": None,
                    "M HA.pdf": None,
                    "M HA 22-06-2021.pdf": None,
                    "2021": {
                        "something_lost_3.pdf": None,
                        "PH HA 24-06-2021.pdf": None,
                        "PH 2 HA.pdf": None,
                        "M 2 HA.pdf": None,
                        "M HA 23-06-2021.pdf": None,
                        "Juni": {
                            "PH HA 25-06-2021.pdf": None,
                            "text1.pdf": None,
                            "PH Materialien": {  # just not a duplicate of 'PH Material'
                                "text1.pdf": None,
                                "PH 3 HA 22-06-2021.pdf": None
                            }
                        }
                    }
                },
                "Mathe": {
                    "2021": {
                        "Juni": {
                            "M HA 24-06-2021.pdf": None
                        }
                    }
                }
            }
        }
        expected = {
            "HAs": {
                "test1.pdf": None,
                "test2.pdf": None,
            },
            "Archive": {
                "something_lost.pdf": None,
                "Physik": {
                    "something_lost_2.pdf": None,
                    "2021": {
                        "something_lost_3.pdf": None,
                        "Juni": {
                            "PH HA 23-06-2021.pdf": None,
                            "PH HA 24-06-2021.pdf": None,
                            "PH HA 25-06-2021.pdf": None,
                            "text1.pdf": None,
                            "PH Materialien": {
                                "text1.pdf": None,
                                "PH 3 HA 22-06-2021.pdf": None
                            }
                        }
                    }
                },
                "Mathe": {
                    "2021": {
                        "Juni": {
                            "M HA 22-06-2021.pdf": None,
                            "M HA 23-06-2021.pdf": None,
                            "M HA 24-06-2021.pdf": None,
                        }
                    }
                }
            }
        }
        # no data collision as that'll be in the future (let's see what happens in 2037 🤔)
        expected["Archive"]["Physik"][self.useful_data["year"]][self.useful_data["month"]] = {
            "PH HA.pdf": None,
            "PH 2 HA.pdf": None,
            "PH Material": {
                "text1.pdf": None,
                "PH HA 22-06-2021.pdf": None,
                "text2.pdf": None
            }
        }
        expected["Archive"]["Mathe"][self.useful_data["year"]][self.useful_data["month"]] = {
            "M HA.pdf": None,
            "M 2 HA.pdf": None
        }
        self.setup_root_directory_with_files(structure)

        self.manager.transfer_directory(self.manager.homework_dir)
        self.manager.reorganize_all_files()

        self.evaluate_root_directory_with_files(expected)
