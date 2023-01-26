from os import PathLike
from typing import Dict, List, Tuple
from abc import ABC, abstractmethod

from quaker.core.cache import Cache  # TODO move cache into here
from quaker.core.query import Query


class Parser:
    def __new__(cls, query: Query):
        parser = {
            "csv": CSVParser,
            "text": TextParser,
        }.get(query.format)

        if parser is None:
            raise NotImplementedError()

        return super().__new__(parser)

    def __init__(self, *_):
        self.cache = Cache()

    def __call__(self, download) -> Tuple[List[str], List[str], List[str]]:
        download_lines = download.readlines()
        return (
            self.header(download_lines),
            self.body(download_lines),
            self.footer(download_lines),
        )


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

    def body(self, lines) -> List[str]:
        body = []
        for line in self.records(lines):
            event_id = self.event_record(line)['event_id']

            if event_id not in self.cache:
                body.append(line)
                self.cache.append(event_id)

        return body

    @abstractmethod
    def footer(self, lines) -> List[str]:
        pass


class CSVParser(Parser, BaseParser):
    def __init__(self, *_):
        super().__init__(*_)
        self.delimiter = ","

    def header(self, lines):
        return lines[:1]

    def records(self, lines):
        return lines[1:]

    def event_record(self, line):
        record_values = line.split(self.delimiter)[11]
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
