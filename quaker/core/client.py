import logging
from pathlib import Path
from os import PathLike, path, makedirs, remove
from time import sleep
from typing import Dict, List, Optional, Tuple
from requests import Response
from requests.sessions import Request, Session
from quaker.core.query import Query
from quaker.core.cache import Cache
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
from quaker.core.parser import Parser
from quaker.core.writer import Writer


logger = logging.getLogger(__name__)


class Client:
    def __init__(self):
        self.session = Session()
        self.history = []
        self.cache = None
        self.parser = None
        self.writer = None

    def execute(self, query: Query, output_file: PathLike):
        error_recived = None
        do_cleanup = True
        try:
            # run_query(query, self.session, self.output_file)  # TODO deprecate
            self._execute_paginiated(query, output_file)
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt recieved, safely closing session.")
        except Exception as error:  # pylint: disable=broad-except
            logger.error(f"Unknown error recieved ({repr(error)}), safely closing session.")
            error_recived = error
        else:
            do_cleanup = False

        if do_cleanup and self.writer is not None:
            self.writer.cleanup_output(output_file)

        if error_recived is not None:
            raise error_recived

    def _execute_paginiated(self, query: Query, output_file: PathLike):
        logger.info(f"{output_file=}")
        self.parser = Parser(query)
        self.writer = Writer(output_file)
        self.cache = Cache()

        _page_index = 0
        has_next_page = True
        header, records, footer = [], [], []
        while has_next_page:
            logger.info(f"{_page_index=}")
            if _page_index > 5:
                raise RecursionError()

            limit = query.limit
            query.limit = UPPER_LIMIT if limit is None else min(limit, UPPER_LIMIT)

            logger.info("_execute")
            download = self._execute(query)

            if not download.ok:
                status = download.status_code

                # Break if empty
                if status == RESPONSE_NO_CONTENT:
                    logger.info("No data found, exiting loop")
                    break

                # Crash on unexpected errors
                msg = f"Unexpected response code on query ({status})."
                if status == RESPONSE_BAD_REQUEST:
                    msg = f"Invalid query ({RESPONSE_BAD_REQUEST})."

                logger.error(msg)
                raise RuntimeError(msg)

            logger.info("parse response")
            header, records, footer = self.parser(download)

            if _page_index == 0:
                logger.info("header")
                self.writer(header)

            n_results_raw = len(records)
            logger.info(f"{n_results_raw=}")
            records = self._filter_records(records)
            n_results = len(records)
            logger.info(f"{n_results=}")

            if n_results == 0:
                logger.warning("No new records found on page, exiting loop")
                break

            logger.info("records")
            self.writer(records)

            if n_results_raw < UPPER_LIMIT:
                logger.info("Written last page, exiting loop")
                break

            logger.info("last_record")
            last_record = self.parser.event_record(records[-1])
            if limit is not None:
                limit -= n_results_raw

            logger.info("split_query")
            query = self._next_page(query, last_record, limit)
            _page_index += 1

        logger.info("footer")
        self.writer(footer)

    def _next_page(
        self,
        query: Query,
        last_record: Dict[str, str],
        limit: Optional[int] = None,
    ) -> Query:
        last_time, last_magnitude = last_record["event_time"], last_record["event_magnitude"]
        next_fields = {
            "time": ("starttime", last_time),
            "time-asc": ("endtime", last_time),
            "magnitude": ("maxmagnitude", last_magnitude),
            "magnitude-asc": ("minmagnitude", last_magnitude),
        }
        next_name, next_value = next_fields[query.orderby or "time"]

        query_dict = query.dict()
        query_dict[next_name] = next_value
        query_dict["limit"] = limit

        return Query(**query_dict)

    def _filter_records(self, records) -> List[str]:
        if self.parser is None or self.cache is None:
            raise ValueError()
        body = []
        duplicate_events = 0
        for line in records:
            event_id = self.parser.event_record(line)["event_id"]

            if event_id in self.cache:
                duplicate_events += 1
            else:
                body.append(line)
                self.cache.append(event_id)

        if duplicate_events > 0:
            logger.warning(f"{duplicate_events} found on page")
        return body

    def _execute(self, query: Query) -> Response:  # Based on get_data
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
