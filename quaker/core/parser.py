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
    @staticmethod
    def event_data(line) -> Tuple[str, str, str]:
        """Parse event_id, event_time, event_magnitude from a line."""

    def body(self, lines) -> List[str]:
        body = []
        for line in self.records(lines):
            event_id, *_ = self.event_data(line)

            if event_id not in self.cache:
                body.append(line)
                self.cache.append(event_id)

        return body

    @abstractmethod
    def footer(self, lines) -> List[str]:
        pass


class CSVParser(Parser, BaseParser):
    def header(self, lines):
        return lines[:1]

    def records(self, lines):
        return lines[1:]

    @staticmethod
    def event_id(line):
        return line.split(",")[11]

    def footer(self, _):
        return []


class TextParser(CSVParser):
    def event_id(self, line):
        return line.split("|")[11]
