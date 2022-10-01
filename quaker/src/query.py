"""Classes and methods for representation of queries."""
import re
from dataclasses import dataclass, asdict
from typing import Optional

from quaker.globals import ISO8601_REGEX


@dataclass
class Query:  # pylint: disable=too-many-instance-attributes
    """Class for managing inputs for queries

    API Docs: https://earthquake.usgs.gov/fdsnws/event/1/
    """

    endtime: Optional[str] = None
    starttime: Optional[str] = None
    minlatitude: Optional[float] = None
    minlongitude: Optional[float] = None
    maxlatitude: Optional[float] = None
    maxlongitude: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    maxradiuskm: Optional[float] = None
    limit: Optional[int] = None
    minmagnitude: Optional[int] = None
    maxmagnitude: Optional[int] = None
    limit: Optional[int] = None

    def __post_init__(self):
        for time in [self.starttime, self.endtime]:
            assert (
                time is None or isinstance(time, str) and re.match(ISO8601_REGEX, time)
            ), "Invalid time provided"

        lat_lngs = [
            (self.minlatitude, self.minlongitude),
            (self.maxlatitude, self.maxlongitude),
            (self.latitude, self.longitude),
        ]
        for lat, lng in lat_lngs:
            lat = (float(lat) + 90) % 180 - 90 if lat is not None else None
            lng = (float(lng) + 180) % 360 - 180 if lng is not None else None

        assert self.maxradiuskm is None or 0 < self.maxradiuskm <= 20001.6, "Invalid `maxradiuskm`."
        assert self.limit is None or 0 < self.limit <= 20000, "Invalid `limit`."
        assert self.minmagnitude is None or self.minmagnitude >= 0, "Invalid `minmagnitude`."
        assert self.maxmagnitude is None or self.maxmagnitude >= 0, "Invalid `minmagnitude`."

        assert self.limit is None or self.limit > 0, "Invalid `limit`"

    def __str__(self):
        out = "QueryParams("
        for key, value in asdict(self).items():
            out += "\n" + 4 * " " + f"{key}: {str(value)}"
        out += "\n)"
        return out
