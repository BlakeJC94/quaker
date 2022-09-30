"""Functions for writing data to disk."""
import logging
from os import path

from requests import Request


logger = logging.getLogger(__name__)

# TODO docs
def write_content(download: Request, output_file: str):
    mode = "a" if path.exists(output_file) else "w"
    exit_signal = False
    with open(output_file, mode, encoding="utf-8") as csvfile:
        try:
            lines = download.iter_lines(decode_unicode=True)
            if mode == "a":  # Skip header if appending to file
                _ = next(lines)
            csvfile.writelines(line + "\n" for line in lines)
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt recieved, safely closing session")
            exit_signal = True

    if exit_signal:  # Signal to parent process that keyboard interrupt was received.
        raise KeyboardInterrupt
