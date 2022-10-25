"""Functions for writing data to disk."""
import logging
from os import path
from typing import Optional, Set

from requests import Request

from quaker.core.cache import Cache
from quaker.core.query import Query


logger = logging.getLogger(__name__)


def write_content(
    download: Request,
    output_file: str,
    query: Query,
    last_events: Optional[Cache] = None,
    write_header: bool = True,
    write_footer: bool = True,
) -> Set[str]:
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
        last_events = Cache([])

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
        raise NotImplementedError() # TODO

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

# TODO use last_events
def write_json_lines(file, lines, last_events, write_header, write_footer) -> int:  # TODO type hints
    lines_written = 0
    if not write_header:
        first_line = next(lines)
        _, first_record = first_line.split('[', 1)  # already ends with a comma
        file.write(first_record + "\n")

    for line in lines:
        if "bbox" not in line or write_footer:
            file.write(line + "\n")
            lines_written += 1
            continue

        # clip the last line if write_footer is False
        if not write_footer:
            *record, _ = line.split(']', 2)
            last_record = "]".join(line.split(']')[:2])  # doesnt end with a comma
            file.write(last_record + ",\n")

    return lines_written, last_events


# TODO use last_events
# TODO remove duplicates? use a hash table?
def write_text_lines(file, lines, last_events, write_header) -> int:  # TODO type hints
    lines_written = 0
    if not write_header:
        _ = next(lines)

    for line in lines:
        file.write(line + "\n")
        lines_written += 1

    file.writelines(line + "\n" for line in lines)
    return lines_written, last_events

