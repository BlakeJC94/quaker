"""Script to open a session and stream CSV data."""
import logging
from os import path, makedirs
from typing import Optional

from requests import Session

from quaker.core import run_query, Query

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
    if output_file != "/dev/stdout":
        output_file = path.abspath(output_file)
        if path.exists(output_file):
            logger.error("File exists, remove the file or select a different destination.")
            return None

        parent_dir, _ = path.split(output_file)
        if not path.exists(parent_dir):
            logger.info(f"Creatin dir {parent_dir} doesnt exist, creating.")
            makedirs(parent_dir, exist_ok=True)

    if not isinstance(query, Query):
        # filter kwargs
        query_inputs = {k: v for k, v in kwargs.items() if k in Query.__annotations__}
        query = Query(query_inputs)

    error_recived = None
    with Session() as session:
        try:
            run_query(query, session, output_file)
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt recieved, safely closing session.")
        except Exception as error:  # pylint: disable=broad-except
            logger.error(f"Unknown error recieved ({repr(error)}), safely closing session.")
            error_recived = error

    if error_recived is not None:
        raise error_recived
