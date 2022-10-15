"""Functions for writing data to disk."""
import logging
from os import path

from requests import Request


logger = logging.getLogger(__name__)


def write_content(download: Request, output_file: str, write_header: bool = True) -> None:
    """Write content from a http request.

    Args:
        download: Returned response from request.
        output_file: Location of file to rite results to.
        write_header: Flag controlling whether to write the header to the file.
    """
    mode = "w" if not path.exists(output_file) else "a"
    error_recived = None
    with open(output_file, mode, encoding="utf-8") as csvfile:
        try:
            # DEBUG
            lines = download.iter_lines(decode_unicode=True)
            for _ in range(2):  # TODO investigate infinite loop further
                *seps, _ = next(lines).split(',', 3)
                logger.info(f"WRITING FILE: {[i for i in seps]}")

            lines = download.iter_lines(decode_unicode=True)
            if not write_header:
                _ = next(lines)
            csvfile.writelines(line + "\n" for line in lines)
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt recieved, safely closing file.")
        except Exception as error:  # pylint: disable=broad-except
            logger.error("Unknown error recieved, safely closing file.")
            error_recived = error

    if error_recived is not None:  # Signal to process that keyboard interrupt was received.
        raise error_recived
