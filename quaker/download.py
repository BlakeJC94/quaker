"""Script to open a session and stream CSV data."""
import logging
from os import path, makedirs
from typing import Optional

from requests import Session

from quaker.src import run_query, Query

logger = logging.getLogger(__name__)


def download(
    output_file: str,
    query: Optional[Query] = None,
    **kwargs,
) -> None:
    """Main function to download data to a CSV file.

    Also supports querying data via kwargs. See `help(quaker.Query)` for a list of the parameters
    that can be configured.

    Args:
        output_file: Path to file to dump output to.
        query: Configured query dataclass. Defaults to query for all events in last 30 days.
    """
    if path.exists(output_file):
        raise FileExistsError("output_file already exists.")

    parent_dir, _ = path.split(output_file)
    if not path.exists(parent_dir):
        logger.info(f"INFO: parent dir {parent_dir} doesnt exist, creating")
        makedirs(parent_dir, exist_ok=True)

    if not isinstance(query, Query):
        query = Query(**kwargs)

    error_recived = None
    with Session() as session:
        try:
            run_query(query, session, output_file)
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt recieved, safely closing session")
            error_recived = KeyboardInterrupt()
        except Exception as error:  # pylint: disable=broad-except
            logger.error("Unknown error recieved, safely closing file.")
            error_recived = error

    if error_recived:  # Signal to parent process that keyboard interrupt was received.
        raise error_recived
