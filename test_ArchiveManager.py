from pyfakefs.fake_filesystem_unittest import TestCase
from ArchiveManager import (ArchiveManager,
                            InvalidFormattingException,
                            IsCompressedFileException,
                            abbr_to_subject,
                            month_to_dir,
                            blacklist_files,
                            blacklist_ext,
                            treshold_date)
import pytest
import os


class AnyTestCase(TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.manager = ArchiveManager(debug=True)
        try:
            self.fs.remove("/volume2")  # make sure dirs need to be created
        except FileNotFoundError:
            pass
        self.useful_data = {
            "year": str(treshold_date.year),
            "month": month_to_dir[treshold_date.month]
        }


class TestParseFilename(AnyTestCase):
    def test_parse_filename_good_formatting(self):
        s, y, m = self.manager.parse_filename("/volume1/PH HA 22-06-2021.pdf")

        assert s == abbr_to_subject["PH"]
        assert y == "2021"
        assert m == month_to_dir[6]

    def test_parse_filename_partial_formatting(self):
        s, y, m = self.manager.parse_filename(
            "/volume1/PH Klausurvorbereitung.pdf")

        assert s == abbr_to_subject["PH"]
        assert y is None
        assert m is None

    def test_parse_filename_raises_invalid_formatting_exception(self):
        with pytest.raises(InvalidFormattingException):
            s, y, m = self.manager.parse_filename("/volume1/test.pdf")


class TestGetDestinationForFile(AnyTestCase):
    def test_get_destination_for_file_same_origin_and_destination(self):
        s = "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/"\
            + "PH HA 22-06-2021.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest == s

    def test_get_destination_for_file_file_not_in_lowest_level_structure(self):
        s = "/volume2/Hausaufgaben/Archive/Physik/2021/PH HA 22-06-2021.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest == s.replace("/2021/", "/2021/" + month_to_dir[6] + "/")

    def test_get_destination_for_file_filename_not_containing_metadata(self):
        s = "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/test.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest is None

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
            + abbr_to_subject["PH"] + "/2021/" + \
            month_to_dir[6] + "/PH HA 22-06-2021.pdf"

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
            + self.useful_data['year'] + "/" + \
            self.useful_data['month'] + \
            "/PH Klausurvorbereitung.pdf"

        dest = self.manager.get_destination_for_file(s)

        assert dest == expected


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
        s = "/volume2/Hausaufgaben/Archive/Physik/2021/Juni/"\
            + "PH HA 22-06-2021.pdf"
        self.fs.create_file(s)

        self.manager.transfer_file(s)

        assert self.fs.exists(s)
        assert self.manager.transferred_files == []
        assert self.manager.not_transferred_files == []

    def test_transfer_file_uhm_actually_its_a_dir(self):
        root = "/volume2/Hausaufgaben/HAs/PH KW25"
        f_list = ["Text 1.md", "Text 2.txt", "Text 3.pdf"]
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
            return "/volume2/Hausaufgaben/Archive/" + abbr_to_subject['PH'] \
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
            return "/volume2/Hausaufgaben/Archive/" + abbr_to_subject['PH'] \
                + "/"\
                + self.useful_data['year']\
                + "/"\
                + self.useful_data['month']\
                + "/"\
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

    def test_transfer_directory_blacklist_files(self):
        def f(name: str) -> str:
            return "/volume2/Hausaufgaben/HAs"\
                + ("/" if len(name) > 0 else "")\
                + name
        # not sure why i need to do that
        self.fs.create_dir("/volume2/Hausaufgaben/HAs")
        for fname in blacklist_files:
            if len(fname.split(".")) > 0:
                self.fs.create_file(fname)
            else:
                self.fs.create_dir(fname)

        self.manager.transfer_directory(f(""))

        for fname in blacklist_files:
            assert self.fs.exists(fname)

        assert self.manager.not_transferred_files == []
        assert self.manager.transferred_files == []

    def test_transfer_directory_blacklist_ext(self):
        def f(name: str) -> str:
            return "/volume2/Hausaufgaben/HAs"\
                + ("/" if len(name) > 0 else "")\
                + name
        self.fs.create_dir("/volume2/Hausaufgaben/HAs")
        for ext in blacklist_ext:
            self.fs.create_file("hello" + ext)

        self.manager.transfer_directory(f(""))

        for ext in blacklist_ext:
            assert self.fs.exists("hello" + ext)

        assert self.manager.transferred_files == []
        assert self.manager.not_transferred_files == []
