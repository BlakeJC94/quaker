"""Function for recursively querying USGS earthquake API"""
import logging
import re
from datetime import datetime
from pytz import UTC
from dataclasses import asdict
from time import sleep
from typing import Optional, Set

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
from .cache import Cache
from .writer import write_content

logger = logging.getLogger(__name__)


def run_query(
    query: Query,
    session: Session,
    output_file: str,
    last_events: Optional[Cache] = None,
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
    # Check recursion guard
    _index = 0 if _index is None else _index
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
        _ = write_content(
            download,
            output_file,
            query,
            last_events=last_events,
            write_header=write_header,
            write_footer=True,
        )
        return

    # Otherwise, split the query into a capped query and a remainder query
    query_hat = Query(**{**asdict(query).copy(), "limit": UPPER_LIMIT})
    download_hat = get_data(query_hat, session)
    if download_hat.status_code != RESPONSE_OK:
        # Crash if the capped query unexpectedly fails
        msg = f"Unexpected response code on split query: {download.status_code}"
        logger.error(msg)
        raise RuntimeError(msg)

    # Add successful sub-query to stack
    last_events = write_content(
        download_hat,
        output_file,
        query_hat,
        last_events=last_events,
        write_header=write_header,
        write_footer=False,
    )

    # Create remainder query
    remainder = split_query(query, download_hat)

    # (subtract one from recursion index on each recursive call to guard against infinite loop)
    _next_index = _index + 1
    logger.info(f"Starting recursion: {_next_index}")
    run_query(
        remainder,
        session,
        output_file,
        last_events=last_events,
        write_header=False,
        _index=_next_index,
    )
    return None


def split_query(query, download_hat):
    orderby = query.orderby or "time"
    order, *_asc = orderby.split("-")
    order_asc = len(_asc) > 0 and _asc[0] == "asc"

    next_prefixes = ["end", "start"] if order == "time" else ["max", "min"]
    next_param = get_last_param(download_hat, query.format, order)  # TODO fixme

    next_arg = next_prefixes[int(order_asc)] + order
    return Query(**{**asdict(query).copy(), next_arg: next_param})


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


# TODO fix this for xml formats
# kml
#   - Get 4th last line [-4]
#   - xml.etree.ElementTree?
# xml/quakeml
#   - Get 3rd last line [-3]
#   - xml.etree.ElementTree?
def get_last_param(download: Request, file_format: str, order: str) -> str:
    """Get final time value from a request.

    Args:
        download: Successful response from API.

    Returns:
        ISO8601 datetime string.
    """
    last_param = None
    if file_format in ["kml", "xml", "quakeml"]:
        raise NotImplementedError()

    reversed_clipped_content = download.content[::-1].removeprefix(b"\n")
    reversed_last_row = reversed_clipped_content.split(b"\n")[0]
    last_row = reversed_last_row[::-1]

    if file_format in ["csv", "text"]:
        index = 0 if order == "time" else 4
        delim = b"," if file_format == "csv" else b"|"
        last_param = last_row.split(delim)[index].decode().removesuffix('Z')

    if file_format == "geojson":
        index = "time" if order == "time" else "mag"
        last_param = str(re.search(f'"{index}":([^,]+)', last_row.decode("utf-8"))[1])
        if index == "time":
            last_param = datetime.fromtimestamp(int(last_param) * 1e-3, tz=UTC).isoformat()

    return last_param
