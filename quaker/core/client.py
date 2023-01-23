import logging
from os import PathLike, path, makedirs
from time import sleep
from typing import Optional, Union
from requests.sessions import Session
from quaker.core.query import Query
from quaker.core.run import run_query
from quaker.globals import BASE_URL, MAX_ATTEMPTS, RESPONSE_NOT_FOUND, UPPER_LIMIT

logger = logging.getLogger(__name__)


class Client:
    def __init__(self):
        self.session = Session()

    @staticmethod
    def _validate_output_file(output_file: str):
        if output_file == "/dev/stdout":
            return

        output_file = path.abspath(output_file)
        if path.exists(output_file):
            raise FileExistsError("File exists, remove the file or select a different destination.")

        parent_dir, _ = path.split(output_file)
        if not path.exists(parent_dir):
            logger.info(f"Directory {parent_dir} doesnt exist, creating.")
            makedirs(parent_dir, exist_ok=True)

    def execute(self, query: Query, output_file: PathLike):
        self._validate_output_file(output_file)

        error_recived = None
        try:
            # TODO Make run_query a client method (execute_paginiated)
            run_query(query, self.session, self.output_file)
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt recieved, safely closing session.")
        except Exception as error:  # pylint: disable=broad-except
            logger.error(f"Unknown error recieved ({repr(error)}), safely closing session.")
            # TODO cleanup output_file
            error_recived = error

        if error_recived is not None:
            raise error_recived

    def _execute_paginiated(self, query: Query, output_file: PathLike):
        has_next_page = True

        # TODO Keep track of number of records in loop
        # TODO implement __len__ method for result
        if query.limit is not None:
            raise UserWarning("query.limit not supported yet")
            # self._execute()

        # TODO Add history attr for client

        _index = 0
        while has_next_page:
            if _index > 5:
                raise RecursionError()
            # Set limit
            # Exec query
            # Break if empty
            # Write results
            # If output doesn't exist, write header
            # Get order/last field
            # Update query
            # Goto start

        # Check if whole query was empty
        # Write footer of last result

            ...
        ...

    def _execute(self, query: Query):  # Based on get_data
        out = None
        with self.session as session:
            for attempts in range(MAX_ATTEMPTS):
                download = session.get(
                    BASE_URL,
                    params={**query.dict()},
                )
                if download.status_code != RESPONSE_NOT_FOUND:
                    return download
                logger.warning(f"No connection could be made, retrying ({attempts}).")
                sleep(2)

            logger.error("No connection could be made.")
        return out
