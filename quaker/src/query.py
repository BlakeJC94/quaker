"""Classes and methods for representation of queries."""
import re
from dataclasses import dataclass, asdict
from typing import Optional

from quaker.globals import ISO8601_REGEX


# TODO add remaining params
# TODO add timezone handling
# WARNING: doc parsing relies on:
#   * Types are inferred from first arg of `Optional[..]` typing
@dataclass
class Query:  # pylint: disable=too-many-instance-attributes
    """Class for managing inputs for queries

    API Docs: https://earthquake.usgs.gov/fdsnws/event/1/

    NOTE: All times use ISO8601 Date/Time format (yyyy-mm-ddThh:mm:ss). UTC is assumed.
    NOTE: Minimum/maximum longitude values may cross the date line at 180 or -180

    Args:
        endtime: Limit to events on or before the specified end time.
        starttime: Limit to events on or after the specified start time.
        minlatitude: Limit to events with a latitude larger than the specified minimum.
        minlongitude: Limit to events with a longitude larger than the specified minimum.
        maxlatitude: Limit to events with a latitude smaller than the specified maximum.
        maxlongitude: Limit to events with a longitude smaller than the specified maximum.
        latitude: Specify the latitude to be used for a radius search.
        longitude: Specify the longitude to be used for a radius search.
        maxradiuskm: Limit to events within the specified maximum number of kilometers from the
            geographic point defined by the latitude and longitude parameters.
        maxmagnitude: Limit to events with a magnitude smaller than the specified maximum.
        minmagnitude: Limit to events with a magnitude larger than the specified minimum.
        limit: Limit the results to the specified number of events.
    """

    # NOTE: Var type in CLI docs are inferred from `Optional[x]`
    # (first callable type in square brackets, STR if none)
    endtime: Optional[str] = None
    starttime: Optional[str] = None
    minlatitude: Optional[float] = None
    minlongitude: Optional[float] = None
    maxlatitude: Optional[float] = None
    maxlongitude: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    maxradiuskm: Optional[float] = None
    minmagnitude: Optional[int] = None
    maxmagnitude: Optional[int] = None
    limit: Optional[int] = None

    def __post_init__(self):
        for time in [self.starttime, self.endtime]:
            try:
                assert (
                    time is None or isinstance(time, str) and re.match(ISO8601_REGEX, time)
                ), "Invalid time provided"
            except:
                breakpoint()

        lat_lngs = [
            (self.minlatitude, self.minlongitude),
            (self.maxlatitude, self.maxlongitude),
            (self.latitude, self.longitude),
        ]
        for lat, lng in lat_lngs:
            lat = (float(lat) + 90) % 180 - 90 if lat is not None else None
            lng = (float(lng) + 360) % 720 - 360 if lng is not None else None

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
