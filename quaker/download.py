"""Script to open a session and stream CSV data."""
import logging
from os import path, makedirs
from typing import List

from requests import Session, Request

from quaker.src import run_query, Query

logger = logging.getLogger(__name__)


# TODO docstring
def download(query_params: Query, output_file: str) -> List[Request]:
    if path.exists(output_file):
        raise FileExistsError("output_file already exists.")

    parent_dir, _ = path.split(output_file)
    if not path.exists(parent_dir):
        logger.info(f"INFO: parent dir {parent_dir} doesnt exist, creating")
        makedirs(parent_dir, exist_ok=True)

    error_recived = None
    with Session() as session:
        try:
            return run_query(query_params, session, output_file)
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt recieved, safely closing session")
            error_recived = KeyboardInterrupt()
        except Exception as error:  # pylint: disable=broad-except
            logger.error("Unknown error recieved, safely closing file.")
            error_recived = error

    if error_recived:  # Signal to parent process that keyboard interrupt was received.
        raise error_recived
