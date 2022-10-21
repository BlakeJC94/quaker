"""Functions for writing data to disk."""
import logging
from os import path

from requests import Request

from quaker.core.query import Query


logger = logging.getLogger(__name__)


def write_content(
    download: Request,
    output_file: str,
    query: Query,
    write_header: bool = True,
    write_footer: bool = True,
) -> None:
    """Write content from a http request.

    Args:
        download: Returned response from request.
        output_file: Location of file to rite results to.
        query: Metadata for request.
        write_header: Flag controlling whether to write the header to the file.
        write_footer: Flag controlling whether to write the footer to the file.
    """
    file_format = query.format or "csv"  # TODO update this default
    mode = "w" if not path.exists(output_file) else "a"
    error_recived = None
    with open(output_file, mode, encoding="utf-8") as file:
        try:
            lines = download.iter_lines(decode_unicode=True)
            if file_format in ["csv" or "text"]:
                write_text_lines(file, lines, write_header)
            elif file_format == "geojson":
                # raise NotImplementedError() # TODO
                write_json_lines(file, lines, write_header, write_footer)
            elif file_format == "kml":
                raise NotImplementedError() # TODO
            elif file_format in ["xml", "quakeml"]:
                raise NotImplementedError() # TODO
            else:
                raise ValueError()
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt recieved, safely closing file.")
        except Exception as error:  # pylint: disable=broad-except
            logger.error("Unknown error recieved, safely closing file.")
            error_recived = error

    if error_recived is not None:  # Signal to process that keyboard interrupt was received.
        raise error_recived

def write_json_lines(file, lines, write_header, write_footer):  # TODO type hints
    if not write_header:
        first_line = next(lines)
        _, first_record = first_line.split('[', 1)  # already ends with a comma
        file.write(first_record + "\n")

    for line in lines:
        if "bbox" not in line or write_footer:
            file.write(line + "\n")
            continue

        # clip the last line if write_footer is False
        if not write_footer:
            *record, _ = line.split(']', 2)
            last_record = "]".join(line.split(']')[:2])  # doesnt end with a comma
            file.write(last_record + ",\n")


# TODO remove duplicates? use a hash table?
def write_text_lines(file, lines, write_header):  # TODO type hints
    if not write_header:
        _ = next(lines)
    file.writelines(line + "\n" for line in lines)

