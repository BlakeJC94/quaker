import re
from datetime import datetime
from typing import List, Tuple
from abc import ABC, abstractmethod

from requests import Response

from quaker.core.query import Query
from quaker.globals import DEFAULT_FORMAT

# TODO Test
# - [ ] __new__ subclass resolution
# - [ ] Unpack methods w/ mock parser
# - [ ] For each format
#     - [ ] check how a page is parsed

# TODO KmlParser
# TODO XmlParser (same as QuakeML)


class Parser:
    def __new__(cls, query: Query):
        parser = {
            "csv": CSVParser,
            "text": TextParser,
            "geojson": GeojsonParser,
            "xml": XmlParser,
            "quakeml": XmlParser,
            "kml": KmlParser,
        }.get(query.format or DEFAULT_FORMAT)

        if parser is None:
            raise NotImplementedError()

        return super().__new__(parser)

    def unpack_response(self, download: Response) -> Tuple[List[str], List[str], List[str]]:
        lines = download.text.strip().split("\n")
        return (
            self.header(lines),
            self.records(lines),
            self.footer(lines),
        )

    def unpack_records(self, records: List[str]) -> Tuple[List[str], List[str], List[str]]:
        return tuple(zip(*(self.event_record(line) for line in records)))

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


class CSVParser(Parser):
    def header(self, lines):
        return lines[:1]

    def records(self, lines):
        return lines[1:]

    def event_record(self, line):
        record_values = line.split(",")
        return (
            record_values[11],
            record_values[0].removesuffix("Z"),
            record_values[4],
        )

    def footer(self, _):
        return []


class TextParser(Parser):
    def header(self, lines):
        return lines[:1]

    def records(self, lines):
        return lines[1:]

    def event_record(self, line):
        record_values = line.split("|")
        return (
            record_values[0],
            record_values[1],
            record_values[10],
        )

    def footer(self, _):
        return []


class GeojsonParser(Parser):
    def event_record(self, line):
        event_id = re.search(r"\"id\":\"([^,]+)\"", line)[1]
        event_timestamp = re.search(r"\"time\":([^,]+)", line)[1]
        event_magnitude = re.search(r"\"mag\":([^,]+)", line)[1]
        return (
            event_id,
            datetime.utcfromtimestamp(float(event_timestamp) * 1e-3).isoformat(),
            event_magnitude,
        )

    def header(self, lines):
        return [lines[0].split("[", 1)[0] + "["]

    def footer(self, lines):
        return ["]" + "]".join(lines[-1].split("]")[2:]).removesuffix(",")]

    def records(self, lines):
        return [
            lines[0].split("[", 1)[1].removesuffix(","),
            *[l.removesuffix(",") for l in lines[1:-1]],
            "]".join(lines[-1].split("]")[:2]).removesuffix(","),
        ]


class XmlParser(Parser):
    def event_record(self, line):
        event_id = re.search(r"catalog:eventid=\"([^,]+)\"\s", line)[1]
        event_time = re.search(r"<time>.*<value>([^,]+)</value>.*</time>", line)[1]
        event_magnitude = re.search(r"<mag>.*<value>([^,]+)</value>.*</mag>", line)[1]
        return (
            event_id,
            event_time.removesuffix('Z'),
            event_magnitude,
        )

    def header(self, lines):
        return lines[:3]

    def footer(self, lines):
        return lines[-2:]

    def records(self, lines):
        return lines[3:-2]

class KmlParser(Parser):
    def event_record(self, line):
        event_id = re.search(r"id=\"([^,]+)\"", line)[1]
        event_time = re.search(r"<dt>Time</dt><dd>([\d-]+\s[\d:]+)\sUTC</dd>", line)[1]
        event_magnitude = re.search(r"M\s([^,]+)\s-", line)[1]
        return (
            event_id,
            event_time.replace(' ', "T"),
            event_magnitude,
        )

    def header(self, lines):
        return lines[:13]

    def footer(self, lines):
        return lines[-3:]

    def records(self, lines):
        return lines[13:-3]
