"""Functions for writing data to disk."""
import logging
import re
from os import path
from typing import Iterable, Optional, Tuple, TextIO

from requests import Request

from quaker.core.cache import Cache
from quaker.core.query import Query
from quaker.globals import UPPER_LIMIT


logger = logging.getLogger(__name__)


def write_content(
    download: Request,
    output_file: str,
    query: Query,
    last_events: Optional[Cache] = None,
    write_header: bool = True,
    write_footer: bool = True,
) -> Cache:
    """Write content from a http request.

    Args:
        download: Returned response from request.
        output_file: Location of file to rite results to.
        query: Metadata for request.
        write_header: Flag controlling whether to write the header to the file.
        write_footer: Flag controlling whether to write the footer to the file.
    """
    error_recived = None
    if last_events is None:
        last_events = Cache([], maxlen=UPPER_LIMIT)

    writers = {
        "geojson": write_json_lines,
        "csv": write_text_lines,
        "text": write_text_lines,
        "quakeml": None,  # TODO
        "kml": None,  # TODO
        "xml": None,  # TODO
    }

    file_format = query.format
    write = writers[file_format]
    if write is None:
        raise NotImplementedError()

    mode = "w" if not path.exists(output_file) else "a"
    with open(output_file, mode, encoding="utf-8") as file:
        try:
            lines = download.iter_lines(decode_unicode=True)
            lines_written, last_events = write(file, lines, last_events, write_header, write_footer)
            if lines_written == 0:
                raise ValueError(f"No lines were written to {output_file} from {str(query)}")

        except KeyboardInterrupt:
            logger.error("Keyboard interrupt recieved, safely closing file.")

        except Exception as error:  # pylint: disable=broad-except
            logger.error("Unknown error recieved, safely closing file.")
            error_recived = error

    if error_recived is not None:  # Signal to process that keyboard interrupt was received.
        raise error_recived

    return last_events


# TODO: check what happens if there's only one result
# TODO: check what happens if there's no results
def write_json_lines(
    file: TextIO,
    lines: Iterable[str],
    last_events: Cache,
    write_header: bool,
    write_footer: bool,
) -> Tuple[int, Cache]:
    lines_written = 0

    header, footer = None, None
    for line in lines:
        event_id = re.search(r"\"id\":\"([\w\d]+)\"", line)[1]
        if "FeatureCollection" in line:
            header, line = line.split("[", 1)
            header = header + "["

        if "bbox" in line:
            *line, footer = line.split("]", 2)
            line, footer = "]".join(line), "]" + footer

        if header is not None and write_header:
            file.write(header)
            header = None

        line = line.removesuffix(",")
        line = line if footer is not None and write_footer else line + ",\n"

        if event_id not in last_events:
            file.write(line)
            lines_written += 1
            last_events.append(event_id)

        if footer is not None and write_footer:
            file.write(footer + "\n")
            footer = None

    return lines_written, last_events


def write_text_lines(
    file: TextIO,
    lines: Iterable[str],
    last_events: Cache,
    write_header: bool,
    _write_footer: bool,
) -> Tuple[int, Cache]:
    del _write_footer
    lines_written = 0

    first_line = next(lines)
    if write_header:
        file.write(first_line + "\n")

    for line in lines:
        event_id = line.replace(",", "|").split("|")[11]
        if event_id in last_events:
            continue

        file.write(line + "\n")
        lines_written += 1
        last_events.append(event_id)

    return lines_written, last_events
