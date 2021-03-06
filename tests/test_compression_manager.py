from tests.test_config import TESTING_CONFIG
from home_automation import config

from home_automation.compression_middleware import (
    ChangeStatusInThingsMiddleware,
    FlashLightsInHomeAssistantMiddleware
)
from home_automation.compression_manager import CompressionManager
import os
import re
from typing import List

import pytest
import pytest_asyncio


@pytest.mark.usefixtures("do_setup")
class AnyTestCase:
    @pytest_asyncio.fixture
    def do_setup(self, fs):
        self.manager = CompressionManager(
            TESTING_CONFIG, debug=True, testing=True)
        [self.manager.register_middleware(m(TESTING_CONFIG, self.manager.logger)) for m in [
            FlashLightsInHomeAssistantMiddleware,
            ChangeStatusInThingsMiddleware]]
        try:
            fs.rmdir("/volume2")
        except FileNotFoundError:
            pass


def create_file(fs, name: str):
    dest = os.path.join(TESTING_CONFIG.homework_dir, name)
    d, f = os.path.split(dest)
    if not fs.isdir(d):
        fs.create_dir(d)
    fs.create_file(dest)


def file_exists(fs, name: str):
    exists = fs.exists(os.path.join(TESTING_CONFIG.homework_dir, name))
    return exists


@pytest_asyncio.fixture
def configure_mock_responses(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=TESTING_CONFIG.home_assistant.url + "/api/services/script/flash_miguels_room")
    pattern = re.compile(TESTING_CONFIG.things_server.url +
                         r"/api/v1/markhomeworkasdone\?subject=\w{1,2}")
    httpx_mock.add_response(method="POST", url=pattern)


@pytest.mark.asyncio
class TestCompressDirectory(AnyTestCase):

    # TODO: see docstring
    @pytest_asyncio.fixture
    def manager_did_compress_files(self, fs):
        """Only checks logs, not if files are actually being compressed."""
        manager = self.manager

        class ManagerDidTryCompressingFilesHelper:
            def __init__(self):
                self.did_try_to_compress_files = {}
                self.files = {}
                self.did_evaluate = False

            def prepare(self, files: List[str]):
                """Create required files."""
                self.files = files
                for f in files:
                    self.did_try_to_compress_files[f] = False
                    try:
                        create_file(fs, f)
                    except FileExistsError:
                        pass

            def evaluate(self):
                """Assert whether files were compressed.
                Got a better synonyme for 'assert'?"""
                self.did_evaluate = True
                for line in manager.logger._lines:
                    for f in self.files:
                        path = os.path.join(TESTING_CONFIG.homework_dir, f)
                        if f"Compressing '{path}'" in line:
                            self.did_try_to_compress_files[f] = True

                # don't double newlines
                [print(line[:-1]) for line in manager.logger._lines]

                for k, v in self.did_try_to_compress_files.items():
                    assert v, \
                        f"CompressionManager did not try to compress '{k}'"
        return ManagerDidTryCompressingFilesHelper()

    @pytest.mark.usefixtures("configure_mock_responses")
    async def test_compress_directory_is_nondestructive(self, fs):
        files = [
            "PH KW25.pdf",
            "PH HA 22-06-2021.pdf"
            "test.pdf",
            "test.txt"
        ]
        for f in files:
            try:
                create_file(fs, f)
            except FileExistsError:
                pass

        await self.manager.compress_directory(TESTING_CONFIG.homework_dir)

        for f in files:
            assert file_exists(fs, f)

        assert len(fs.listdir(TESTING_CONFIG.homework_dir)) == len(files)

    async def test_compress_directory_is_nondestructive_2(self, fs):
        files = [
            "test.small.pdf",
            "test.small.txt",
            "PH KW25.small.pdf",
            "PH HA 22-06-2021.small.pdf"
        ]
        for f in files:
            try:
                create_file(fs, f)
            except FileExistsError:
                pass

        await self.manager.compress_directory(TESTING_CONFIG.homework_dir)

        for f in files:
            assert file_exists(fs, f)

        assert len(fs.listdir(TESTING_CONFIG.homework_dir)) == len(files)

    async def test_compress_directory_is_nondestructive_3(self, fs):
        files = [
            "test.pdf",
            "test.txt",
            "PH KW25.pdf",
            "PH HA 22-06-2021.pdf",
            "test.small.pdf",
            "test.small.txt",
            "PH KW25.small.pdf",
            "PH HA 22-06-2021.small.pdf"
        ]
        for f in files:
            try:
                create_file(fs, f)
            except FileExistsError:
                pass

        await self.manager.compress_directory(TESTING_CONFIG.homework_dir)

        for f in files:
            assert file_exists(fs, f)

        assert len(fs.listdir(TESTING_CONFIG.homework_dir)) == len(files)

    async def test_compress_directory_blacklists(self, fs, httpx_mock):
        files = [
            "test.txt",
            "test.small.pdf",
            "test.png",
            "test.small.png",
            ".PH HA 22-06-2021.pdf",
            "_PH HA 22-06-2021.pdf",
            "Scan 22-06-2021.pdf",
            "Scanned Document"
        ]
        for f in files:
            try:
                create_file(fs, f)
            except FileExistsError:
                pass

        await self.manager.compress_directory(TESTING_CONFIG.homework_dir)

        for f in files:
            assert file_exists(fs, f)

        assert len(fs.listdir(TESTING_CONFIG.homework_dir)) == len(files)
        assert len(httpx_mock.get_requests()) == 0

    @pytest.mark.usefixtures("configure_mock_responses")
    async def test_compress_directory_compresses_uncompressed_files(
            self, fs, manager_did_compress_files):
        """'Alternative' to actually ensuring files are getting compressed.
        See `test_compress_directory_compresses_uncompressed_files`."""
        files = [
            "test.pdf",
            "PH KW25.pdf",
            "PH HA 22-06-2021.pdf"
        ]
        manager_did_compress_files.prepare(files)

        await self.manager.compress_directory(TESTING_CONFIG.homework_dir)

        manager_did_compress_files.evaluate()

    @pytest.mark.usefixtures("configure_mock_responses")
    async def test_compress_directory_compresses_directories(
            self, fs, manager_did_compress_files):
        files = [
            "test.pdf",
            "PH Material/text1.pdf",
            "PH Material/text2.pdf",
            "PH Material/PH KW25.pdf"
        ]
        manager_did_compress_files.prepare(files)

        await self.manager.compress_directory(TESTING_CONFIG.homework_dir)

        manager_did_compress_files.evaluate()

    @pytest.mark.usefixtures("configure_mock_responses")
    async def test_compress_directory_compresses_directories_and_handles_subfiles_appropriately(self, fs, manager_did_compress_files, httpx_mock):
        files = [
            "PH Material/text1.pdf",
            "PH Material/PH KW25.pdf"
        ]
        hass_url = f"{TESTING_CONFIG.home_assistant.url}/api/services/" + \
            "script/flash_miguels_room"
        expected = [
            hass_url,
            hass_url,
            f"{TESTING_CONFIG.things_server.url}/api/v1/markhomeworkasdone?subject=PH"
        ]
        manager_did_compress_files.prepare(files)

        await self.manager.compress_directory(TESTING_CONFIG.homework_dir)

        manager_did_compress_files.evaluate()

        requests = httpx_mock.get_requests()
        assert len(requests) == len(expected)
        for r in requests:
            assert str(r.url) in expected

    @pytest.mark.usefixtures("configure_mock_responses")
    async def test_compress_directory_tries_to_flash_lights(self,
                                                            fs,
                                                            httpx_mock):
        files = [
            ".PH HA 22-06-2021.pdf",
            "_PH HA 22-06-2021.pdf",
            "PH HA 22-06-2021.pdf",
            "PH HA 22-06-2021.small.pdf",
            "K HA 23-06-2021.pdf",
            "SP HA 24-06-2021.pdf"
        ]
        for f in files:
            try:
                create_file(fs, f)
            except FileExistsError:
                pass

        await self.manager.compress_directory(TESTING_CONFIG.homework_dir)

        requests = httpx_mock.get_requests()
        # only ones which are valid (not on blacklist like (\.|_)*) and
        # where there isn't a compressed version already
        filtered = list(filter(lambda r: str(r.url).startswith(
            TESTING_CONFIG.home_assistant.url), requests))
        assert len(filtered) == 2

    @pytest.mark.usefixtures("configure_mock_responses")
    async def test_compress_directory_tries_to_check_homework(self,
                                                              fs,
                                                              httpx_mock):
        files = [
            ".PH HA 22-06-2021.pdf",
            "_PH HA 22-06-2021.pdf",
            "PH HA 22-06-2021.pdf",
            "PH HA 22-06-2021.small.pdf",
            "PH HA 23-06-2021.pdf",
            "PH HA 24-06-2021.pdf",
            "IF HA 22-06-2021.pdf",
            "M HA 22-06-2021.pdf"
        ]
        for f in files:
            try:
                create_file(fs, f)
            except FileExistsError:
                pass
        expected = {
            "PH": 2,
            "IF": 1,
            "M": 1
        }

        await self.manager.compress_directory(TESTING_CONFIG.homework_dir)

        result = {}
        requests = httpx_mock.get_requests()
        for request in requests:
            subject = request.url.params.get("subject", None)
            if subject is not None:
                value = result.get(subject, None)
                if value is None:
                    result[subject] = 1
                else:
                    result[subject] += 1

        assert result == expected


class TestCleanUpDirectory(AnyTestCase):
    def test_clean_up_directory(self, fs):
        files = [
            ".PH HA 22-06-2021.pdf",
            ".PH HA 22-06-2021.small.pdf",
            "_PH HA 22-06-2021.pdf",
            "PH HA 22-06-2021.pdf",
            "test.pdf",
            "test.txt"
        ]
        for f in files:
            try:
                create_file(fs, f)
            except FileExistsError:
                pass
        # referring to `files`: files up to this idx are supposed to be deleted
        idx_up_to_files_to_be_kept = 3

        self.manager.clean_up_directory(TESTING_CONFIG.homework_dir)

        for f in files[:idx_up_to_files_to_be_kept]:
            assert not file_exists(fs, f)
        for f in files[idx_up_to_files_to_be_kept:]:
            assert file_exists(fs, f)

        assert len(fs.listdir(TESTING_CONFIG.homework_dir)) == len(
            files[idx_up_to_files_to_be_kept:])
