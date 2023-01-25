import logging
from os import PathLike, path, makedirs
from time import sleep
from typing import Optional, Union
from requests.sessions import Session
from quaker.core.query import Query
from quaker.core.run import run_query
from quaker.globals import (
    BASE_URL,
    MAX_ATTEMPTS,
    RESPONSE_BAD_REQUEST,
    RESPONSE_NO_CONTENT,
    RESPONSE_NOT_FOUND,
    RESPONSE_OK,
    UPPER_LIMIT,
    STDOUT,
)


logger = logging.getLogger(__name__)


class Client:
    def __init__(self):
        self.session = Session()
        self.history = []

    @staticmethod
    def _validate_output_file(output_file: PathLike):
        if output_file == STDOUT:
            return

        output_file = path.abspath(output_file)
        if path.exists(output_file):
            raise FileExistsError("File exists, remove the file or select a different destination.")

        parent_dir, _ = path.split(output_file)
        if not path.exists(parent_dir):
            logger.info(f"Directory {parent_dir} doesnt exist, creating.")
            makedirs(parent_dir, exist_ok=True)

    @staticmethod
    def cleanup_output(output_file: PathLike):
        if output_file != STDOUT and path.exists(output_file):
            remove(output_file)

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
            error_recived = error
        finally:
            self.cleanup_output(output_file)

        if error_recived is not None:
            raise error_recived

    def _execute_paginiated(self, query: Query, output_file: PathLike):
        has_next_page = True

        # TODO create writer class (resolve format to subclass)
        writer = Writer(output_file, format=query.format)

        # TODO Keep track of number of records in loop
        # TODO implement __len__ method for result
        if query.limit is not None:
            raise UserWarning("query.limit not supported yet")
            # self._execute()

        _index = 0
        while has_next_page:
            if _index > 5:
                raise RecursionError()

            query.limit = UPPER_LIMIT
            result = self._execute(query)
            status = result.download.status_code

            # Break if empty
            if status == RESPONSE_NO_CONTENT:
                logger.info("No data found, exiting loop")
                break

            # Crash on unexpected errors
            if status != RESPONSE_OK:
                if status == RESPONSE_BAD_REQUEST:
                    msg = f"Invalid query given query ({RESPONSE_BAD_REQUEST})."
                else:
                    msg = f"Unexpected response code on query ({status})."
                logger.error(msg)
                raise RuntimeError(msg)

            # Write results
            # TODO add writer methods on __call__
            # TODO writer logic, eg If output doesn't exist, write header
            writer(result)

            # Get order/last field
            # Update query
            # Goto start

        # Check if whole query was empty
        # Write footer of last result

            ...
        ...

    def _execute(self, query: Query) -> Result:  # Based on get_data
        self.history.append(query)

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
