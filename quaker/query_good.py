"""..."""
import re
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional, Union, List
from warnings import warn

import requests
import pandas as pd


BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
OUTPUT_CSV = "./data/output/foo.csv"

ISO8601_REGEX = r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\+\d{2}:d{2})?)?(\.\d{6})?$"
ISO8601_DT_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

MAX_DEPTH = 3
RESPONSE_BAD_REQUEST = 400
RESPONSE_OK = 200
UPPER_LIMIT = 20000
DEFAULT_QUERY_PARAMS = {"format": "csv", "orderby": "time"}


@dataclass
class QueryParams:
    """Class for managing inputs for queries

    API Docs: https://earthquake.usgs.gov/fdsnws/event/1/
    """

    endtime: Optional[str] = None
    starttime: Optional[str] = None
    minlatitude: Optional[float] = None
    minlongitude: Optional[float] = None
    maxlatitude: Optional[float] = None
    maxlongitude: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    maxradiuskm: Optional[float] = None
    limit: Optional[int] = None
    minmagnitude: Optional[int] = None
    maxmagnitude: Optional[int] = None
    limit: Optional[int] = None

    def __post_init__(self):
        for time in [self.starttime, self.endtime]:
            assert (
                time is None or isinstance(time, str) and re.match(ISO8601_REGEX, time)
            ), "Invalid time provided"

        lat_lngs = [
            (self.minlatitude, self.minlongitude),
            (self.maxlatitude, self.maxlongitude),
            (self.latitude, self.longitude),
        ]
        for lat, lng in lat_lngs:
            lat = (float(lat) + 90) % 180 - 90 if lat is not None else None
            lng = (float(lng) + 180) % 360 - 180 if lng is not None else None

        assert (
            self.maxradiuskm is None or 0 < self.maxradiuskm <= 20001.6
        ), "Invalid `maxradiuskm`."
        assert self.limit is None or 0 < self.limit <= 20000, "Invalid `limit`."
        assert (
            self.minmagnitude is None or self.minmagnitude >= 0
        ), "Invalid `minmagnitude`."
        assert (
            self.maxmagnitude is None or self.maxmagnitude >= 0
        ), "Invalid `minmagnitude`."

        assert self.limit is None or self.limit > 0, "Invalid `limit`"

    def __str__(self):
        out = "QueryParams("
        self_dict = asdict(self)
        for key, value in asdict(self).items():
            out += "\n" + 4 * " " + f"{key}: {str(value)}"
        out += "\n)"
        return out


def get_data(query_params, session) -> requests.Request:
    return session.get(
        BASE_URL,
        params={**DEFAULT_QUERY_PARAMS, **asdict(query_params)},
    )


def get_last_time(download):
    reversed_clipped_content = download.content[:1:-1]
    reversed_last_row = reversed_clipped_content.split(b"\n")[1]
    last_row = reversed_last_row[::-1]
    last_row_first_col = last_row.split(b",")[0]
    return datetime.strptime(
        last_row_first_col.decode("utf-8"),
        ISO8601_DT_FORMAT + "Z",
    )


def write_content(download, output_file):
    mode = "a" if os.path.exists(output_file) else "w"
    with open(output_file, mode, encoding="utf-8") as csvfile:
        lines = download.iter_lines(decode_unicode=True)
        if mode == "a":  # Skip header if appending to file
            _ = next(lines)
        csvfile.writelines(line + "\n" for line in lines)


def run_query(query, session, output_file, _recursion_index=MAX_DEPTH):

    # Check recursion guard
    if _recursion_index < 1 or _recursion_index > MAX_DEPTH:
        warn(f"Exceeded maximum recursion depth {MAX_DEPTH}.")
        return None

    if _recursion_index == MAX_DEPTH:
        # check if output path exists, eremove if needed
        if os.path.exists(output_file):
            print("output file already exists, removing")
            os.remove(output_file)
    else:
        print(f"Remaining recursions: {_recursion_index}")

    # Try input query
    download = get_data(query, session)

    # Exit if there's an unexpected error
    if download.status_code not in [RESPONSE_OK, RESPONSE_BAD_REQUEST]:
        raise RuntimeError(f"Unexpected response code on query: {download.status_code}")

    # If successful, add it to the memory stack and return
    if download.status_code == RESPONSE_OK:
        write_content(download, output_file)
        return None

    # Otherwise, split the query into a capped query and a remainder query
    query_hat = QueryParams(**{**asdict(query).copy(), "limit": UPPER_LIMIT})
    download_hat = get_data(query_hat, session)
    if download_hat.status_code != RESPONSE_OK:
        raise RuntimeError(
            f"Unexpected response code on split query: {download.status_code}"
        )

    # Add successful query to stack
    write_content(download_hat, output_file)

    # Create remainder query and recurse
    next_endtime = get_last_time(download_hat) + timedelta(microseconds=1)
    next_endtime = next_endtime.strftime(ISO8601_DT_FORMAT)
    remainder = QueryParams(**{**asdict(query).copy(), "endtime": next_endtime})

    # (subtract one from recursion index on each recursive call to guard against infinite loop)
    return run_query(remainder, session, output_file, _recursion_index - 1)


def download_data(query_params: QueryParams, output_file) -> List[requests.Request]:
    with requests.Session() as session:
        return run_query(query_params, session, output_file)


# >>>> TRY SMALL QUERY
fields = {
    "starttime": "2022-09-27",
}
qp = QueryParams(**fields)
downloads = download_data(qp, output_file=OUTPUT_CSV)
print("Done!..")
# <<<<


# >>>> TRY LARGE QUERY
fields = {
    "starttime": "2022-05-27",
}
qp = QueryParams(**fields)
downloads = download_data(qp, output_file=OUTPUT_CSV)
print("Done!..")
# <<<<

foo = pd.read_csv(OUTPUT_CSV)
