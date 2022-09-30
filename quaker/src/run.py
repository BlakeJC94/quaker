"""Function for recursively querying USGS earthquake API"""
import os
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Optional, Union, List
from warnings import warn

from requests import Request

from quaker import Query
from quaker.globals import (
    MAX_DEPTH,
    RESPONSE_OK,
    RESPONSE_BAD_REQUEST,
    UPPER_LIMIT,
    ISO8601_DT_FORMAT,
    BASE_URL,

)
from .writer import write_content


# TODO docs
# TODO typehint
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
    query_hat = Query(**{**asdict(query).copy(), "limit": UPPER_LIMIT})
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
    remainder = Query(**{**asdict(query).copy(), "endtime": next_endtime})

    # (subtract one from recursion index on each recursive call to guard against infinite loop)
    return run_query(remainder, session, output_file, _recursion_index - 1)


# TODO docs
# TODO typehint
def get_data(query_params, session) -> Request:
    return session.get(
        BASE_URL,
        params={**DEFAULT_QUERY_PARAMS, **asdict(query_params)},
    )


# TODO docs
# TODO typehint
def get_last_time(download):
    reversed_clipped_content = download.content[:1:-1]
    reversed_last_row = reversed_clipped_content.split(b"\n")[1]
    last_row = reversed_last_row[::-1]
    last_row_first_col = last_row.split(b",")[0]
    return datetime.strptime(
        last_row_first_col.decode("utf-8"),
        ISO8601_DT_FORMAT + "Z",
    )
