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
        # TODO clip
        # `{"type":"FeatureCollection","metadata":{"generated":1666040106000,"url":"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&endtime=2022-09-02&starttime=2022-09-01","title":"USGS Earthquakes","status":200,"api":"1.13.6","count":386},"features":[`
        # from first line
        _ = next(lines)

    for line in lines:
        if "bbox" not in line:
            file.write(line + "\n")
            continue
        if not write_footer:
            # TODO clip line
            file.write(line + "\n")

    if not write_footer:
        # TODO Replace
        # `],"bbox":[-178.8919,-57.9804,-3.19,179.54833333333,66.579,574.627]}`
        # with `,\n` in file before writing
        file.writelines(line + "\n" for line in lines)
    # TODO


# TODO remove duplicates? use a hash table?
def write_text_lines(file, lines, write_header):  # TODO type hints
    if not write_header:
        _ = next(lines)
    file.writelines(line + "\n" for line in lines)

