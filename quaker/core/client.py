from io import StringIO
import logging
from pathlib import Path
from os import PathLike, path, makedirs, remove
from time import sleep
from typing import Dict, List, Optional, Tuple
from requests import Response
from requests.sessions import Request, Session
from quaker.core.query import Query
from quaker.core.record_filter import RecordFilter
from quaker.globals import (
    BASE_URL,
    MAX_ATTEMPTS,
    RESPONSE_BAD_REQUEST,
    RESPONSE_NO_CONTENT,
    RESPONSE_NOT_FOUND,
    UPPER_LIMIT,
    MAX_PAGES,
)
from quaker.core.parser import Parser
from quaker.core.writer import Writer
import pandas as pd


logger = logging.getLogger(__name__)

class Client:
    def __init__(self):
        self.session = Session()
        self.history = []

    def execute(self, query: Query, output_file: Optional[PathLike] = None) -> Optional[pd.DataFrame]:
        if output_file is None:
            query.format = "csv"

        results = self._get_results(query)
        output, error_recived = self._write_results(results, output_file, query)

        if error_recived is not None:
            raise error_recived

        return output

    def _get_results(self, query):
        results = []
        try:
            results = self._execute_paginiated(query)
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt recieved, safely closing session.")
        return results

    @staticmethod
    def _write_results(results, output_file, query):
        logger.info(f"{output_file=}")
        writer = None if output_file is None else Writer(output_file, query)

        output = None
        do_cleanup, error_recived = True, None
        try:
            if writer is None:
                output = pd.read_csv(StringIO("\n".join(results)))
            else:
                writer(results)
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt recieved, safely closing file.")
        except Exception as error:  # pylint: disable=broad-except
            logger.error(f"Unknown error recieved ({repr(error)}), safely closing file.")
            error_recived = error
        else:
            do_cleanup = False

        if do_cleanup and writer is not None:
            writer.cleanup_output()

        return output, error_recived

    def _execute_paginiated(self, query: Query) -> List[str]:
        results = []
        parser, record_filter = Parser(query), RecordFilter([], maxlen=UPPER_LIMIT)

        header, records_raw, records, footer = [], [], [], []
        page_index, has_next_page = 0, True
        while has_next_page:
            logger.info(f"{page_index=}")
            if page_index >= MAX_PAGES:
                logger.error("Hit page limit, exiting loop")
                break

            limit = query.limit
            query.limit = UPPER_LIMIT if limit is None else min(limit, UPPER_LIMIT)

            logger.info("_execute")
            download = self._execute(query)

            empty_page = False
            if not download.ok:
                empty_page = self._check_download_error(download.status_code)

            logger.info("parse response")
            header, records_raw, footer = parser.unpack_response(download)

            if page_index == 0:
                logger.info("header")
                results += header

            if len(records_raw) == 0:
                logger.info("empty page found")
                empty_page = True
                has_next_page = False

            if not empty_page:
                (
                    event_ids,
                    event_times,
                    event_magnitudes,
                ) = parser.unpack_records(records_raw)
                records = record_filter(records_raw, event_ids)
                has_next_page = self._check_filtered_results(records, records_raw)
                has_next_page = self._check_valid_magnitude_results(query, event_magnitudes)
                logger.info("records")
                results += records

            if has_next_page:
                logger.info("split_query")
                limit = None if limit is None else limit - len(records_raw)
                query = self._next_page(query, event_times[-1], event_magnitudes[-1], limit)
                page_index += 1

        logger.info("footer")
        results += footer

        return results

    @staticmethod
    def _check_filtered_results(records_filtered, records) -> bool:
        has_next_page = True
        n_results, n_results_raw = len(records_filtered), len(records)
        logger.info(f"{n_results_raw=}")
        logger.info(f"{n_results=}")
        if (duplicate_events := n_results - n_results_raw) > 0:
            logger.warning(f"{duplicate_events} found on page")
        if n_results == 0:
            logger.warning("No new records found on page, exiting loop")
            has_next_page = False
        if n_results_raw < UPPER_LIMIT:
            logger.info("Written last page, exiting loop")
            has_next_page = False
        return has_next_page

    @staticmethod
    def _check_valid_magnitude_results(query, event_magnitudes) -> bool:
        has_next_page = True
        if (
            query.orderby is not None
            and query.orderby.removesuffix("-asc") == "magnitude"
            and len(set(event_magnitudes)) == 1
        ):
            logger.warning(
                "Page contains only one magnitude value, so cannot determine "
                "next page. Exiting loop."
            )
            has_next_page = False
        return has_next_page

    @staticmethod
    def _check_download_error(status):
        # Break if empty
        if status == RESPONSE_NO_CONTENT:
            logger.info("No data found, exiting loop")
            return True

        # Crash on unexpected errors
        msg = f"Unexpected response code on query ({status})."
        if status == RESPONSE_BAD_REQUEST:
            msg = f"Invalid query ({RESPONSE_BAD_REQUEST})."

        logger.error(msg)
        raise RuntimeError(msg)

    def _next_page(
        self,
        query: Query,
        last_time,
        last_magnitude,
        limit: Optional[int] = None,
    ) -> Query:
        next_fields = {
            "time": ("endtime", last_time),
            "time-asc": ("starttime", last_time),
            "magnitude": ("maxmagnitude", last_magnitude),
            "magnitude-asc": ("minmagnitude", last_magnitude),
        }
        next_name, next_value = next_fields[query.orderby or "time"]

        query_dict = query.dict()
        query_dict[next_name] = next_value
        query_dict["limit"] = limit

        return Query(**query_dict)

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
