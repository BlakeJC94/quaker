import pytest
import pandas as pd
from requests import Session

from quaker.globals import BASE_URL, RESPONSE_OK
from quaker.core.query import Query
from quaker.core.client import Client


class TestClient:
    @staticmethod
    def assert_files_equal(filepath_1, filepath_2):
        with (
            open(filepath_1, "r", encoding="utf-8") as file1,
            open(filepath_2, "r", encoding="utf-8") as file2,
        ):
            assert file1.read() == file2.read()

    @staticmethod
    def create_mock_request(status_code, fixture_path):
        if fixture_path is None:
            return dict(status_code=status_code)
        with open(fixture_path, "r", encoding="utf-8") as f:
            return dict(text=f.read(), status_code=status_code)

    def load_mock_requests(self, requests_mock, fixture_data):
        assert isinstance(fixture_data, list)
        assert len(fixture_data) > 0
        assert len(fixture_data[0]) == 2
        requests = [self.create_mock_request(st, fp) for st, fp in fixture_data]
        requests_mock.get(BASE_URL, requests)
        return requests_mock

    @pytest.mark.parametrize("multi_page", [False, True])
    def test_execute_dataframe(self, requests_mock, mocker, multi_page):
        mocker.patch('quaker.core.client.UPPER_LIMIT', 20)
        n_pages, expected_filename = (1, "single_page") if not multi_page else (3, "multi_page")

        fixture_data = [
            (RESPONSE_OK, f"./tests/fixtures/results/page{k}.csv")
            for k in range(n_pages)
        ]
        expected_file = f"./tests/fixtures/expected/{expected_filename}.csv"
        self.load_mock_requests(requests_mock, fixture_data=fixture_data)

        client = Client()
        mock_query = Query()

        output = client.execute(mock_query)
        expected = pd.read_csv(expected_file)

        assert output.equals(expected)

    @pytest.mark.parametrize("query_format", ["csv", "text", "geojson", "xml", "quakeml", "xml"])
    @pytest.mark.parametrize("multi_page", [False, True])
    def test_exectute_output_file(self, mocker, requests_mock, tmp_path, query_format, multi_page):
        mocker.patch('quaker.core.client.UPPER_LIMIT', 20)

        output_file = tmp_path / f"test_execute.{query_format}"
        n_pages, expected_filename = (1, "single_page") if not multi_page else (3, "multi_page")

        fixture_data = [
            (RESPONSE_OK, f"./tests/fixtures/results/page{k}.{query_format}")
            for k in range(n_pages)
        ]
        expected_file = f"./tests/fixtures/expected/{expected_filename}.{query_format}"
        self.load_mock_requests(requests_mock, fixture_data=fixture_data)

        client = Client()
        mock_query = Query(format=query_format)

        client.execute(mock_query, output_file=output_file)

        self.assert_files_equal(output_file, expected_file)
