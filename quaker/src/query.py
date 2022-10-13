"""Classes and methods for representation of queries."""
import re
from dataclasses import dataclass, asdict
from typing import Optional

from quaker.globals import ISO8601_REGEX

ALLOWED_VALUES = {

}


# TODO add remaining params
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
    format: Optional[str] = None  # TODO
    # Time
    endtime: Optional[str] = None
    starttime: Optional[str] = None
    updatedafter: Optional[str] = None # TODO
    # Location - rectangle
    minlatitude: Optional[float] = None
    minlongitude: Optional[float] = None
    maxlatitude: Optional[float] = None
    maxlongitude: Optional[float] = None
    # Location - circle
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    maxradiuskm: Optional[float] = None
    # Other
    catalog: Optional[str] = None  # TODO
    contributor: Optional[str] = None  # TODO
    eventid: Optional[str] = None  # TODO
    includeallmagnitudes: Optional[bool] = None  # TODO
    includeallorigins: Optional[bool] = None  # TODO
    includearrivals: Optional[bool] = None  # TODO
    includedeleted: Optional[bool] = None  # TODO
    includesuperceded: Optional[bool] = None  # TODO
    limit: Optional[int] = None
    maxdepth: Optional[int] = None  # TODO
    maxmagnitude: Optional[int] = None
    mindepth: Optional[int] = None  # TODO
    minmagnitude: Optional[int] = None
    offset: Optional[int] = None  # TODO
    orderby: Optional[str] = None  # TODO
    # Extensions
    alertlevel: Optional[str] = None  # TODO
    callback: Optional[str] = None  # TODO
    eventtype: Optional[str] = None  # TODO
    jsonerror: Optional[str] = None  # TODO
    kmlanimated: Optional[str] = None  # TODO
    kmlcolorby: Optional[str] = None  # TODO
    maxcdi: Optional[str] = None  # TODO
    maxgap: Optional[str] = None  # TODO
    maxmmi: Optional[str] = None  # TODO
    maxsig: Optional[str] = None  # TODO
    mincdi: Optional[str] = None  # TODO
    minfelt: Optional[int] = None  # TODO
    mingap: Optional[float] = None  # TODO
    minsig: Optional[int] = None  # TODO
    nodata: Optional[int] = None  # TODO
    productype: Optional[str] = None  # TODO
    produccode: Optional[str] = None  # TODO
    reviewstatus: Optional[str] = None  # TODO

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
