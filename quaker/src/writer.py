"""Functions for writing data to disk."""
import logging
from os import path

from requests import Request


logger = logging.getLogger(__name__)


def write_content(download: Request, output_file: str) -> None:
    """Write content from a http request.

    Args:
        download: Returned response from request.
        output_file: Location of file to rite results to.
    """
    mode = "a" if path.exists(output_file) else "w"
    error_recived = None
    with open(output_file, mode, encoding="utf-8") as csvfile:
        try:
            lines = download.iter_lines(decode_unicode=True)
            if mode == "a":  # Skip header if appending to file
                _ = next(lines)
            csvfile.writelines(line + "\n" for line in lines)
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt recieved, safely closing file")
            error_recived = KeyboardInterrupt()
        except Exception as error:  # pylint: disable=broad-except
            logger.error("Unknown error recieved, safely closing file.")
            error_recived = error

    if error_recived:  # Signal to parent process that keyboard interrupt was received.
        raise error_recived
