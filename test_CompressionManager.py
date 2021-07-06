from CompressionManager import (
    CompressionManager,
    root,
    home_assistant_url,
    home_assistant_token,
    things_server_url
)
import pytest
import os
import httpx
import re


@pytest.mark.usefixtures("do_setup")
class AnyTestCase:
    @pytest.fixture
    def do_setup(self, fs):
        self.manager = CompressionManager(debug=True, testing=True)
        try:
            fs.rmdir("/volume2")
        except FileNotFoundError:
            pass

    def create_file(self, fs, name: str):
        dest = os.path.join(root, name)
        d, f = os.path.split(dest)
        if not fs.isdir(d):
            fs.create_dir(d)
        fs.create_file(dest)

    def file_exists(self, fs, name: str):
        exists = fs.exists(os.path.join(root, name))
        return exists


@pytest.mark.asyncio
class TestCompressDirectory(AnyTestCase):
    @pytest.fixture
    def configure_mock_responses(self, httpx_mock):
        httpx_mock.add_response(
            method="POST",
            url=home_assistant_url + "/api/services/script/flash_miguels_room")
        pattern = re.compile(things_server_url +
                             r"/api/v1/markhomeworkasdone\?subject=\w{1,2}")
        httpx_mock.add_response(method="POST", url=pattern)

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
                self.create_file(fs, f)
            except FileExistsError:
                pass

        await self.manager.compress_directory(root)

        for f in files:
            assert self.file_exists(fs, f)

        assert len(fs.listdir(root)) == len(files)

    async def test_compress_directory_is_nondestructive_2(self, fs):
        files = [
            "test.small.pdf",
            "test.small.txt",
            "PH KW25.small.pdf",
            "PH HA 22-06-2021.small.pdf"
        ]
        for f in files:
            try:
                self.create_file(fs, f)
            except FileExistsError:
                pass

        await self.manager.compress_directory(root)

        for f in files:
            assert self.file_exists(fs, f)

        assert len(fs.listdir(root)) == len(files)

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
                self.create_file(fs, f)
            except FileExistsError:
                pass

        await self.manager.compress_directory(root)

        for f in files:
            assert self.file_exists(fs, f)

        assert len(fs.listdir(root)) == len(files)

    async def test_compress_directory_blacklists(self, fs, httpx_mock):
        files = [
            "test.txt",
            "test.small.pdf",
            "test.png",
            "test.small.png",
            ".PH HA 22-06-2021.pdf",
            "_PH HA 22-06-2021.pdf",
            "Scan 22-06-2021.pdf"
        ]
        for f in files:
            try:
                self.create_file(fs, f)
            except FileExistsError:
                pass

        await self.manager.compress_directory(root)

        for f in files:
            assert self.file_exists(fs, f)

        assert len(fs.listdir(root)) == len(files)
        assert len(httpx_mock.get_requests()) == 0

    @pytest.mark.xfail(True,
                       reason="Ghostscript doesn't use fake files. "
                       + "Cannot say if they're getting compressed.")
    @pytest.mark.usefixtures("configure_mock_responses")
    async def test_compress_directory_compresses_uncompressed_files(self, fs):
        files = [
            "test.pdf",
            "PH KW25.pdf",
            "PH HA 22-06-2021.pdf"
        ]
        for f in files:
            try:
                self.create_file(fs, f)
            except FileExistsError:
                pass

        await self.manager.compress_directory(root)

        for f in files:
            assert self.file_exists(fs, f)
            assert self.file_exists(fs, f.replace(".pdf", ".small.pdf"))

        assert len(fs.listdir(root)) == 2*len(files)

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
                self.create_file(fs, f)
            except FileExistsError:
                pass

        await self.manager.compress_directory(root)

        requests = httpx_mock.get_requests()
        # only ones which are valid (not on blacklist like (\.|_)*) and
        # where there isn't a compressed version already
        filtered = list(filter(lambda r: str(r.url).startswith(
            home_assistant_url), requests))
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
                self.create_file(fs, f)
            except FileExistsError:
                pass
        expected = {
            "PH": 2,
            "IF": 1,
            "M": 1
        }

        await self.manager.compress_directory(root)

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
                self.create_file(fs, f)
            except FileExistsError:
                pass
        # referring to `files`: files up to this idx are supposed to be deleted
        idx_up_to_files_to_be_kept = 3

        self.manager.clean_up_directory(root)

        for f in files[:idx_up_to_files_to_be_kept]:
            assert not self.file_exists(fs, f)
        for f in files[idx_up_to_files_to_be_kept:]:
            assert self.file_exists(fs, f)

        assert len(fs.listdir(root)) == len(
            files[idx_up_to_files_to_be_kept:])


class TestCommunicationSystems:

    def test_handle_response_valid(self):
        r = httpx.Response(status_code=200, content="Successful.")
        s = "Hello, world!"
        manager = CompressionManager()

        manager._handle_response(r, s)

        assert s in manager.logger._lines[-1]

    def test_handle_response_not_found(self):
        s = "Not found."
        r = httpx.Response(status_code=404, content=s)
        manager = CompressionManager()

        manager._handle_response(r, s)  # s doesn't matter

        assert s in manager.logger._lines[-1]

    # Can't use the httpx_mock fixture in a class?

    @pytest.mark.asyncio
    async def test_flashes_lights_in_home_assistant(self, httpx_mock):
        httpx_mock.add_response(method="POST", url=home_assistant_url +
                                "/api/services/script/flash_miguels_room")
        manager = CompressionManager()

        await manager.flash_lights_in_home_assistant()

        assert "flash_lights_in_home_assistant" in manager.logger.context
        assert "Flashed lights." in manager.logger._lines[-1]
        req = httpx_mock.get_request()
        assert req.headers["authorization"] == "Bearer " + home_assistant_token

    @pytest.mark.asyncio
    async def test_changes_status_in_things(self, httpx_mock):
        """Of course, only check whether a valid request to Things server is
        made."""
        s = "PH"
        pattern = re.compile(things_server_url +
                             r"/api/v1/markhomeworkasdone\?subject=\w{1,2}")
        httpx_mock.add_response(method="POST", url=pattern)
        manager = CompressionManager()

        await manager.change_status_in_things(s)

        assert "change_status_in_things" in manager.logger.context
        assert f"Checked homework ({s}) in Things." in \
            manager.logger._lines[-1]
