"""Classes and methods for representation of queries."""
import logging
import re
from dataclasses import dataclass, asdict, field, fields
from typing import Union, get_origin, get_args

from quaker.globals import ISO8601_REGEX

logger = logging.getLogger(__name__)

ALLOWED_VALUES = dict(
    format=lambda v: v in ["csv", "geojson", "kml", "quakeml", "text", "xml"],
    endtime=lambda v: re.match(ISO8601_REGEX, v),
    starttime=lambda v: re.match(ISO8601_REGEX, v),
    updatedafter=lambda v: re.match(ISO8601_REGEX, v),
    minlatitude=lambda v: -90 <= v <= 90,
    minlongitude=lambda v: -360 <= v <= 360,
    maxlatitude=lambda v: -90 <= v <= 90,
    maxlongitude=lambda v: -360 <= v <= 360,
    latitude=lambda v: -90 <= v <= 90,
    longitude=lambda v: -180 <= v <= 180,
    maxradius=lambda v: 0 <= v <= 180,
    maxradiuskm=lambda v: 0 <= v <= 20001.6,
    includedeleted=lambda v: isinstance(v, bool) or v == "only",
    limit=lambda v: 1 <= v <= 20000,
    maxdepth=lambda v: -100 <= v <= 1000,
    mindepth=lambda v: -100 <= v <= 1000,
    offest=lambda v: v >= 1,
    orderby=lambda v: v in ["time", "time-asc", "magnitude", "magnitude-asc"],
    alertlevel=lambda v: v in ["green", "yellow", "orange", "red"],
    kmlcolorby=lambda v: v in ["age", "depth"],
    maxcdi=lambda v: 0 <= v <= 12,
    maxgap=lambda v: 0 <= v <= 360,
    maxmmi=lambda v: 0 <= v <= 12,
    mincdi=lambda v: 0 <= v <= 12,
    minfelt=lambda v: v >= 1,
    mingap=lambda v: 0 <= v <= 360,
    reviewstatus=lambda v: v in ["all", "automatic", "reviewed"],
)

query_field = field(default=None)


# TODO add timezone handling
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

    # Format
    format: str = query_field
    # Time
    endtime: str = query_field
    starttime: str = query_field
    updatedafter: str = query_field
    # Location - rectangle
    minlatitude: float = query_field
    minlongitude: float = query_field
    maxlatitude: float = query_field
    maxlongitude: float = query_field
    # Location - circle
    latitude: float = query_field
    longitude: float = query_field
    maxradius: float = query_field
    maxradiuskm: float = query_field
    # Other
    catalog: str = query_field
    contributor: str = query_field
    eventid: str = query_field
    includeallmagnitudes: bool = query_field
    includeallorigins: bool = query_field
    includedeleted: Union[bool, str] = query_field
    includesuperceded: bool = query_field
    limit: int = query_field
    maxdepth: float = query_field
    maxmagnitude: float = query_field
    mindepth: float = query_field
    minmagnitude: float = query_field
    offset: int = query_field
    orderby: str = query_field
    # Extensions
    alertlevel: str = query_field
    callback: str = query_field
    eventtype: str = query_field
    jsonerror: bool = query_field
    kmlanimated: bool = query_field
    kmlcolorby: str = query_field
    maxcdi: float = query_field
    maxgap: float = query_field
    maxmmi: float = query_field
    maxsig: int = query_field
    mincdi: str = query_field
    minfelt: int = query_field
    mingap: float = query_field
    minsig: int = query_field
    producttype: str = query_field
    productcode: str = query_field
    reviewstatus: str = query_field

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
