from os import PathLike
from typing import Dict, List, Tuple
from abc import ABC, abstractmethod

from requests import Response

from quaker.core.cache import Cache  # TODO move cache into here
from quaker.core.query import Query
from quaker.globals import DEFAULT_FORMAT


class Parser:
    def __new__(cls, query: Query):
        parser = {
            "csv": CSVParser,
            "text": TextParser,
        }.get(query.format or DEFAULT_FORMAT)

        if parser is None:
            raise NotImplementedError()

        return super().__new__(parser)

    def parse_response(self, download: Response) -> Tuple[List[str], List[str], List[str]]:
        lines = download.text.removesuffix('\n').split('\n')
        return (
            self.header(lines),
            self.records(lines),
            self.footer(lines),
        )

    def __call__(self, result: Union[Response, List[str]]) -> Tuple[List[str], List[str], List[str]]:
        if isinstance(result, Response):
            return self.parse_response(result)
        return tuple(zip(*(self.event_record(line) for line in result)))

class BaseParser(ABC):
    @abstractmethod
    def header(self, lines) -> List[str]:
        pass

    @abstractmethod
    def records(self, lines) -> List[str]:
        pass

    @abstractmethod
    def event_record(self, line) -> Tuple[str, str, str]:
        """Parse event_id, event_time, event_magnitude from a line."""

    @abstractmethod
    def footer(self, lines) -> List[str]:
        pass

class CSVParser(Parser, BaseParser):
    def __init__(self, *_):
        self.delimiter = ","

    def header(self, lines):
        return lines[:1]

    def records(self, lines):
        return lines[1:]

    def event_record(self, line):
        record_values = line.split(self.delimiter)
        return {
            "event_id": record_values[11],
            "event_time": record_values[0],
            "event_magnitude": record_values[4],
        }

    def footer(self, _):
        return []


class TextParser(CSVParser):
    def __init__(self, *_):
        super().__init__(*_)
        self.delimiter = "|"
