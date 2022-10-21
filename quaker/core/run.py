"""Function for recursively querying USGS earthquake API"""
import logging
import json
from dataclasses import asdict
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
        write_content(download, output_file, query, write_header, write_footer=True)
        return None

    # Otherwise, split the query into a capped query and a remainder query
    query_hat = Query(**{**asdict(query).copy(), "limit": UPPER_LIMIT})
    download_hat = get_data(query_hat, session)
    if download_hat.status_code != RESPONSE_OK:
        # Crash if the capped query unexpectedly fails
        msg = f"Unexpected response code on split query: {download.status_code}"
        logger.error(msg)
        raise RuntimeError(msg)

    # Add successful sub-query to stack
    write_content(download_hat, output_file, query_hat, write_header, write_footer=False)

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

    order, *_asc = query.orderby.split('-')
    order_asc = len(_asc) > 0 and _asc[0] == 'asc'

    if order == 'time':
        next_prefixes = ['end', 'start']
    elif order == "magnitude":
        # NOTE: this may fail if looking over a large timespan and
        # more than 20000 events have the same magnitude.
        # Maybe I would raise an error in writer when this happens?
        # TODO eliminate duplicates before/as writing? raise error if nothing to write
        next_prefixes = ['max', 'min']
        # TODO get last magnitude from download_hat
        # next_param = ...
        raise NotImplementedError()
    else:
        raise ValueError()

    next_prefixes = ['end', 'start'] if order == 'time' else ['max', 'min']
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



# TODO fix this for non-csv formats!
# csv is fairly easy
#   - get last line, col 0: time, col 4: mag
# geojson, parse as dict? json.loads? whole damn hings needs to be loaded it seems
#   - get last line of file (foo)
#   - bar = json.loads(']'.join(foo.split(']', 2)[:2]))
#   - bar['properties']['time'] or bar['properties']['mag']
# kml
#   - Get 4th last line [-4]
#   - xml.etree.ElementTree?
# text
#   - similar to csv, split on '|' instead of ','
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
    if file_format in ['kml', 'xml', 'quakeml']:
        raise NotImplementedError()

    reversed_clipped_content = download.content[:1:-1]
    reversed_last_row = reversed_clipped_content.split(b"\n")[1]
    last_row = reversed_last_row[::-1]

    if file_format in ['csv', 'text']:
        index = 0 if order == 'time' else 4
        delim = b"," if file_format == 'csv' else b"|"
        last_param = last_row.split(delim)[index]

    if file_format == 'geojson':
        index = 'time' if order == 'time' else 'mag'
        last_record = json.loads(']'.join(last_row.split(']', 2)[:2]))
        last_param = last_record['properties'][index]

    return last_param
