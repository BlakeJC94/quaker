from typing import List, Tuple
from abc import ABC, abstractmethod

from quaker.core.cache import Cache  # TODO move cache into here


class Parser:
    def __new__(cls, *args, **kwargs):
        query_format = kwargs.get("query_format") or next(
            arg for arg in args if isinstance(arg, str)
        )
        parser = {
            "csv": CSVParser,
            "text": TextParser,
        }.get(query_format)

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
    def records(self, line) -> List[str]:
        pass

    @abstractmethod
    @staticmethod
    def event_id(line) -> str:
        # get event_id
        pass

    def body(self, lines) -> List[str]:
        body = []
        for line in self.records(lines):
            if self.event_id(line) not in self.cache:
                body.append(line)
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
