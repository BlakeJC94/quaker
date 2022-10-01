"""Function for recursively querying USGS earthquake API"""
import logging
from dataclasses import asdict
from datetime import datetime, timedelta
from time import sleep

from requests import Request, Session

from quaker.globals import (
    BASE_URL,
    DEFAULT_QUERY_PARAMS,
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
    max_api_calls: int = MAX_DEPTH,
) -> None:
    """Recursive function to query the USGS API.

    Args:
        query: Query dataclass object.
        session: Session class for connection.
        output_file: Path to destination file.
        max_api_calls: Maximum number of calls to API.
    """
    # Check recursion guard
    if max_api_calls < 1:
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
        raise RuntimeError(f"Unexpected response code on query: {download.status_code}")

    # If successful, add it to the memory stack and return
    if download.status_code == RESPONSE_OK:
        write_content(download, output_file)
        return None

    # Otherwise, split the query into a capped query and a remainder query
    query_hat = Query(**{**asdict(query).copy(), "limit": UPPER_LIMIT})
    download_hat = get_data(query_hat, session)
    if download_hat.status_code != RESPONSE_OK:
        # Crash if the capped query unexpectedly fails
        raise RuntimeError(f"Unexpected response code on split query: {download.status_code}")

    # Add successful query to stack
    write_content(download_hat, output_file)

    # Create remainder query
    next_endtime = get_last_time(download_hat) + timedelta(microseconds=1)
    next_endtime = next_endtime.strftime(ISO8601_DT_FORMAT)
    remainder = Query(**{**asdict(query).copy(), "endtime": next_endtime})

    # (subtract one from recursion index on each recursive call to guard against infinite loop)
    logger.info(f"Remaining recursions: {max_api_calls - 1}")
    run_query(remainder, session, output_file, max_api_calls - 1)


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
            params={**DEFAULT_QUERY_PARAMS, **asdict(query)},
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
