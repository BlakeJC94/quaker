from io import StringIO
import logging
from pathlib import Path
from os import PathLike, path, makedirs, remove
from time import sleep
from typing import Dict, List, Optional, Tuple
from requests import Response
from requests.sessions import Request, Session
from quaker.core.query import Query
from quaker.core.cache import Cache, RecordFilter
from quaker.core.run import run_query
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

    def execute(self, query: Query, output_file: Optional[PathLike]) -> Optional[pd.DataFrame]:
        if output_file is None:
            query.format = "csv"

        error_recived, results, status_ok = None, [], False
        try:
            # run_query(query, self.session, self.output_file)  # TODO deprecate
            results = self._execute_paginiated(query)
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt recieved, safely closing session.")
        except Exception as error:  # pylint: disable=broad-except
            logger.error(f"Unknown error recieved ({repr(error)})")
            raise error

        if not status_ok:
            if error_recived is not None:
                raise error_recived
            return None

        logger.info(f"{output_file=}")
        output, writer, do_cleanup = None, None, True
        try:
            if writer is None:
                output = pd.readcsv(StringIO("\n".join(results)))
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
            writer.cleanup_output(output_file)

        if error_recived is not None:
            raise error_recived

        return output

    def _execute_paginiated(self, query: Query) -> List[str]:
        results = []
        parser, record_filter = Parser(query), RecordFilter()

        header, records, footer = [], [], []
        page_index, has_next_page = 0, True
        while has_next_page:
            logger.info(f"{page_index=}")
            if page_index >= MAX_PAGES:
                logger.info("Hit page limit, exiting")
                break

            n_results_raw = 0
            limit = query.limit
            query.limit = UPPER_LIMIT if limit is None else min(limit, UPPER_LIMIT)

            logger.info("_execute")
            download = self._execute(query)

            empty_page = False
            if not download.ok:
                status = download.status_code

                # Break if empty
                if status == RESPONSE_NO_CONTENT:
                    logger.info("No data found, exiting loop")
                    empty_page = True

                # Crash on unexpected errors
                msg = f"Unexpected response code on query ({status})."
                if status == RESPONSE_BAD_REQUEST:
                    msg = f"Invalid query ({RESPONSE_BAD_REQUEST})."

                logger.error(msg)
                raise RuntimeError(msg)

            logger.info("parse response")
            header, records, footer = parser.unpack_response(download)
            event_ids, event_times, event_magnitudes = parser.unpack_records(records)

            if page_index == 0:
                logger.info("header")
                results += header

            n_results_raw = len(records)
            logger.info(f"{n_results_raw=}")
            if n_results_raw == 0:
                logger.info("empty page found")
                empty_page = True
                has_next_page = False

            if not empty_page:

                if (
                    query.orderby.removesuffix("-asc") == "magnitude"
                    and len(set(event_magnitudes)) == 1
                ):
                    logger.warning(
                        "Page contains only one magnitude value, so cannot determine "
                        "next page. Exiting loop."
                    )
                    has_next_page = False

                records = record_filter(records, event_ids)
                n_results = len(records)
                logger.info(f"{n_results=}")
                if (duplicate_events := n_results - n_results_raw) > 0:
                    logger.warning(f"{duplicate_events} found on page")
                if n_results == 0:
                    logger.warning("No new records found on page, exiting loop")
                    has_next_page = False

                logger.info("records")
                results += records

                if n_results_raw < UPPER_LIMIT:
                    logger.info("Written last page, exiting loop")
                    has_next_page = False

            if has_next_page:
                logger.info("last_record")
                last_record = (event_ids[-1], event_times[-1], event_magnitudes[-1])
                if limit is not None:
                    limit -= n_results_raw

                logger.info("split_query")
                query = self._next_page(query, last_record, limit)
                page_index += 1

        logger.info("footer")
        results += footer

        return results

    def _next_page(
        self,
        query: Query,
        last_record: Dict[str, str],
        limit: Optional[int] = None,
    ) -> Query:
        last_time, last_magnitude = last_record["event_time"], last_record["event_magnitude"]
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
