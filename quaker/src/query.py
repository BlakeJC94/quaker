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
        format: Specify the output format (one of "csv", "geojson", "kml", "quakeml", "text",
            or "xml").

        [Time]
        endtime: Limit to events on or before the specified end time.
        starttime: Limit to events on or after the specified start time.
        updatedafter: Limit to events updated after the specified time.

        [Location - rectangle]
        minlatitude: Limit to events with a latitude larger than the specified minimum [-90, 90].
        minlongitude: Limit to events with a longitude larger than the specified minimum [-360,
            360].
        maxlatitude: Limit to events with a latitude smaller than the specified maximum [-90, 90].
        maxlongitude: Limit to events with a longitude smaller than the specified maximum [-360,
            360].

        [Location - circle]
        latitude: Specify the latitude to be used for a radius search [-90, 90].
        longitude: Specify the longitude to be used for a radius search [-180, 180].
        maxradius: Limit to events within the specified maximum number of degrees from the
            geographic point defined by the latitude and longitude parameters [0, 180].
        maxradiuskm: Limit to events within the specified maximum number of kilometers from the
            geographic point defined by the latitude and longitude parameters [0, 20001.6].

        [Other]
        catalog: Limit to events from a specified catalog.
        contributor: Limit to events contributed by a specified contributor.
        eventid: Select a specific event by ID; event identifiers are data center specific.
        includeallmagnitudes: Specify if all magnitudes for the event should be included.
        includeallorigins: Specify if all origins for the event should be included.
        includedeleted: Specify if deleted products and events should be included. The value "only"
            returns only deleted events.
        includesuperceded: Specify if superseded products should be included. This also includes
            all deleted products, and is mutually exclusive to the includedeleted parameter.
        limit: Limit the results to the specified number of events.
        maxdepth: Limit to events with depth less than the specified maximum.
        maxmagnitude: Limit to events with a magnitude smaller than the specified maximum.
        mindepth: Limit to events with depth more than the specified minimum.
        minmagnitude: Limit to events with a magnitude larger than the specified minimum.
        offset: Return results starting at the event count specified, starting at 1.
        orderby: Order the results (one of "time", "time-asc", "magnitude", or "magnitude-asc").

        [Extensions]
        alertlevel: Limit to events with a specific PAGER alert level (one of "green", "yellow",
            "orange", or "red").
        callback: Convert GeoJSON output to a JSONP response using this callback.
        eventtype: Limit to events of a specific type
        jsonerror: Request JSON(P) formatted output even on API error results. (only for geojson
            format)
        kmlanimated: Whether to include timestamp in generated kml, for google earth animation
            support.
        kmlcolorby: How earthquakes are colored (one of "age", "depth").
        maxcdi: Maximum value for Maximum Community Determined Intensity reported by DYFI [0, 12].
        maxgap: Limit to events with no more than this azimuthal gap [0, 360].
        maxmmi: Maximum value for Maximum Modified Mercalli Intensity reported by ShakeMap [0, 12].
        maxsig: Limit to events with no more than this significance.
        mincdi: Minimum value for Maximum Community Determined Intensity reported by DYFI [0, 12].
        minfelt: Limit to events with this many DYFI responses.
        mingap: Limit to events with no less than this azimuthal gap [0, 360].
        minsig: Limit to events with no less than this significance.
        producttype: Limit to events that have this type of product associated.
        productcode: Return the event that is associated with the productcode.
        reviewstatus: Limit to events with a specific review status (one of "all",
            "automatic", or "reviewed").
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

        # Auto-typecast input values
        bad_values = {}
        for query_field in fields(self):
            name = query_field.name
            val_type = query_field.type
            value = getattr(self, name)

            # Handle generic subtypes, get first parameterised type
            if get_origin(val_type) is not None:
                val_type = get_args(val_type)[0]

            # Typecast values
            if value is not None and not isinstance(value, val_type):
                setattr(self, name, val_type(value))

            # Ensure conditions on parameters are satisfied
            if name in ALLOWED_VALUES and value is not None and not ALLOWED_VALUES[name](value):
                bad_values[name] = value

        if len(bad_values) > 0:
            for name, value in bad_values.items():
                logger.error(f"Invalid value for `{name}`, (got {value})")
            raise AssertionError("Bad values given to query.")

        assert (
            self.maxradiuskm is None or self.maxradius is None
        ), "Only one of `maxradiuskm` and `maxradius` allowed to be specified."

        if self.includedeleted is not None:
            supported_formats = ["csv", "geojson"]
            assert (
                self.format in supported_formats
            ), f"Only formats {supported_formats} allow `includedeleted` to be specified."

        if self.includesuperceded is not None:
            assert (
                self.eventid is not None
            ), "Parameter `includesuperceded` only works when `eventid` is given."

        if self.callback is not None:
            assert self.format == "geojson", "Parameter `callback` only supported for geojson."

        if self.jsonerror is not None:
            assert self.format == "geojson", "Parameter `jsonerror` only supported for geojson."

        if self.kmlcolorby is not None:
            assert self.format == "kml", "Parameter `kmlcolorby` only supported for kml."

        if self.kmlanimated is not None:
            assert self.format == "kml", "Parameter `kmlanimated` only supported for kml."

    def __str__(self):
        out = "QueryParams("
        for key, value in asdict(self).items():
            out += "\n" + 4 * " " + f"{key}: {str(value)}"
        out += "\n)"
        return out
