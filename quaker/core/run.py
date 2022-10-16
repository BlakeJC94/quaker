"""Function for recursively querying USGS earthquake API"""
import logging
from dataclasses import asdict
from datetime import datetime, timedelta
from time import sleep
from typing import Optional

from requests import Request, Session

from quaker.globals import (
    BASE_URL,
    ISO8601_DT_FORMAT,
    MAX_ATTEMPTS,
    MAX_DEPTH,
    RESPONSE_BAD_REQUEST,
    RESPONSE_NOT_FOUND,
    RESPONSE_NO_CONTENT,
    RESPONSE_OK,
    UPPER_LIMIT,
)
from .query import Query
from .writer import write_content

logger = logging.getLogger(__name__)


def run_query(
    query: Query,
    session: Session,
    output_file: str,
    write_header: bool = True,
    _index: Optional[int] = None,
) -> None:
    """Recursive function to query the USGS API.

    Args:
        query: Query dataclass object.
        session: Session class for connection.
        output_file: Path to destination file.
        write_header: Flag controlling whether to write the header to the file.
    """
    _index = 0 if _index is None else _index
    # Check recursion guard
    if _index >= MAX_DEPTH:
        logger.warning("Exceeded maximum recursion depth.")
        return None

    # Try input query
    download = get_data(query, session)

    # Exit if no data is found
    if download.status_code == RESPONSE_NO_CONTENT:
        logger.warning("No data found.")
        return None
    # Crash if there's an unexpected error
    if download.status_code not in [RESPONSE_OK, RESPONSE_BAD_REQUEST]:
        msg = f"Unexpected response code on query: {download.status_code}"
        logger.error(msg)
        raise RuntimeError(msg)

    # If successful, add it to the memory stack and return
    if download.status_code == RESPONSE_OK:
        write_content(download, output_file, write_header)
        return None

    # Otherwise, split the query into a capped query and a remainder query
    query_hat = Query(**{**asdict(query).copy(), "limit": UPPER_LIMIT})
    download_hat = get_data(query_hat, session)
    if download_hat.status_code != RESPONSE_OK:
        # Crash if the capped query unexpectedly fails
        msg = f"Unexpected response code on split query: {download.status_code}"
        logger.error(msg)
        raise RuntimeError(msg)

    # Add successful query to stack
    write_content(download_hat, output_file, write_header)

    # Create remainder query
    remainder = split_query(query, download_hat)

    # (subtract one from recursion index on each recursive call to guard against infinite loop)
    _next_index = _index + 1
    logger.info(f"Starting recursion: {_next_index}")
    run_query(remainder, session, output_file, write_header=False, _index=_next_index)
    return None


def split_query(query, download_hat):
    # TODO check `orderby` attribute
    #   - if time or time-asc, get last time from download_hat
    #     - if time, set last time as new endtime
    #     - if time-asc, set last time as new starttime
    #   - if magnitude or magnitude-asc, get last magnitude from download_hat
    #     - if magnitude, set last magnitude as new maxmagnitude
    #     - if magnitude-asc, set last magnitude as new minmagnitude
    # TODO match on event id and trim duplicates
    next_endtime = get_last_time(download_hat) + timedelta(microseconds=1)
    next_endtime = next_endtime.strftime(ISO8601_DT_FORMAT)
    return Query(**{**asdict(query).copy(), "endtime": next_endtime})


def get_data(query: Query, session: Session) -> Request:
    """Parse URL from query and use session to retrieve response.

    If a 404 error is encountered, download will re-try the download (up to MAX_ATTEMPTS).

    Args:
        query (Query):
        session (Session):

    Returns:
        Results from query request.
    """
    download = None
    for attempts in range(MAX_ATTEMPTS):
        download = session.get(
            BASE_URL,
            params={**asdict(query)},
        )
        if download.status_code != RESPONSE_NOT_FOUND:
            return download
        logger.warning(f"No connection could be made, retrying ({attempts}).")
        sleep(2)

    logger.error("No connection could be made.")
    return download


def get_last_time(download: Request) -> str:
    """Get final time value from a request.

    Args:
        download: Successful response from API.

    Returns:
        ISO8601 datetime string.
    """
    reversed_clipped_content = download.content[:1:-1]
    reversed_last_row = reversed_clipped_content.split(b"\n")[1]
    last_row = reversed_last_row[::-1]
    last_row_first_col = last_row.split(b",")[0]
    return datetime.strptime(
        last_row_first_col.decode("utf-8"),
        ISO8601_DT_FORMAT + "Z",
    )
