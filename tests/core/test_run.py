from unittest import mock
from typing import Union
from pathlib import Path

import pytest
from requests import Session

from quaker.globals import BASE_URL, RESPONSE_OK
from quaker.core import run_query, Query


class MockRequest:
    """Mock class for testing `run_query`."""

    def __init__(self, status_code: int = 200, data: Union[str, Path] = ""):
        self.status_code = status_code
        assert isinstance(data, (str, Path)), "Only strings, or paths are accepted for `data`."

        self.data = data

    def iter_lines(self, decode_unicode: bool = True):
        if isinstance(self.data, str):
            lines = self.data.split("\n")
            for i, line in enumerate(lines):
                if i < len(lines) - 1:
                    line += "\n"
                yield line if decode_unicode else line.encode()
        if isinstance(self.data, Path):
            with open(self.data, "r", encoding="utf-8") as f:
                for line in f.readlines():
                    yield line if decode_unicode else line.encode()


class TestMockRequest:
    status_code = 123
    data_lines = ["this", "is", "mock", "data"]

    @pytest.fixture
    def mock_data_path(self, tmp_path):
        data_path = tmp_path / "mock_data.txt"
        with open(data_path, "w") as f:
            for i, line in enumerate(self.data_lines):
                f.write(line)
                if i < len(self.data_lines) - 1:
                    f.write("\n")

        return data_path

    @staticmethod
    def assert_request_status_and_lines_equal(mock_request, expected_status_code, expected_lines):
        assert mock_request.status_code == expected_status_code
        for i, line in enumerate(mock_request.iter_lines(decode_unicode=True)):
            if i < len(expected_lines) - 1:
                assert line == expected_lines[i] + "\n"
            else:
                assert line == expected_lines[i]

    def test_mock_request_str_data(self):
        data = "\n".join(self.data_lines)
        request = MockRequest(self.status_code, data)
        self.assert_request_status_and_lines_equal(
            request,
            self.status_code,
            self.data_lines,
        )

    def test_mock_request_path_data(self, mock_data_path):
        request = MockRequest(self.status_code, mock_data_path)
        self.assert_request_status_and_lines_equal(
            request,
            self.status_code,
            self.data_lines,
        )


# TODO Ensure multi page query works
# TODO Rename run_query to execute
class TestRunQuery:
    @staticmethod
    def assert_files_equal(filepath_1, filepath_2):
        with (
            open(filepath_1, "r", encoding="utf-8") as file1,
            open(filepath_2, "r", encoding="utf-8") as file2,
        ):
            assert file1.read() == file2.read()

    @staticmethod
    def load_mock_request(requests_mock, status_code, fixture_path):
        with open(fixture_path, "r", encoding="utf-8") as f:
            requests_mock.get(BASE_URL, status_code=status_code, text=f.read())

    def test_single_page_query(self, requests_mock, tmp_path):
        """Query with less than MAX_RESULTS"""
        fixture_path = "./tests/fixtures/foo.csv"
        output_file = tmp_path / "test_single_page.csv"
        query = Query(format="csv")

        self.load_mock_request(requests_mock, RESPONSE_OK, fixture_path)

        with Session() as session:
            run_query(query, session, output_file)

        self.assert_files_equal(output_file, fixture_path)

        assert len(requests_mock.request_history) == 1
        assert str(requests_mock.request_history[0]) == (
            f"GET {BASE_URL}?"
            + "&".join([f"{k}={v}" for k, v in query.dict().items()])
        )

    def test_multi_page_query(self, requests_mock, tmp_path):
        """Query with more than MAX_RESULTS"""
        fixture_path = "./tests/fixtures/foo.csv"
        output_file = tmp_path / "test_multi_page.csv"
        query = Query(format="csv")

        self.load_mock_request(requests_mock, RESPONSE_BAD_REQUEST, fixture_path)
        self.load_mock_request(requests_mock, RESPONSE_OK, fixture_path)
        self.load_mock_request(requests_mock, RESPONSE_OK, fixture_path)
        # TODO verify sequence of gets
        # https://requests-mock.readthedocs.io/en/latest/matching.html
        breakpoint()

        with Session() as session:
            run_query(query, session, output_file)

        breakpoint()
        self.assert_files_equal(output_file, fixture_path)

        assert len(requests_mock.request_history) == 1
        assert str(requests_mock.request_history[0]) == (
            f"GET {BASE_URL}?"
            + "&".join([f"{k}={v}" for k, v in query.dict().items()])
        )
