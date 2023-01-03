from abc import ABC, abstractproperty
from typing import List

from requests.sessions import Request


class BaseResult(ABC):
    def __init__(self, download: Request, has_next_page: bool = False):
        self.has_next_page = has_next_page
        self.lines = list(download.iterlines(decode_unicode=True))

    @abstractproperty
    def header(self) -> str:
        pass

    @abstractproperty
    def body(self) -> List[str]:
        pass

    @abstractproperty
    def footer(self) -> str:
        pass


class CSVResult(BaseResult):
    pass


class Result:
    format_results = {
        "geojson": None,  # TODO
        "csv": CSVResult,
        "text": None,  # TODO
        "quakeml": None,  # TODO
        "kml": None,  # TODO
        "xml": None,  # TODO
    }

    def __new__(cls, format: str):
        if (result_type := cls.format_results.get(format, None)) is None:
            raise NotImplementedError()
        super().__new__(result_type)
