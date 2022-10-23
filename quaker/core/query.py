"""Classes and methods for representation of queries."""
import logging
from dataclasses import dataclass, asdict, field, fields
from datetime import datetime as dt
from typing import Union, get_origin, get_args

logger = logging.getLogger(__name__)


def is_valid_time(time: str):
    valid = True
    try:
        dt.fromisoformat(time)
    except ValueError:
        valid = False
    return valid


ALLOWED_VALUES = dict(
    format=lambda v: v in ["csv", "geojson", "kml", "quakeml", "text", "xml"],
    endtime=is_valid_time,
    starttime=is_valid_time,
    updatedafter=is_valid_time,
    minlatitude=lambda v: -90 <= v <= 90,
    minlongitude=lambda v: -360 <= v <= 360,
    maxlatitude=lambda v: -90 <= v <= 90,
    maxlongitude=lambda v: -360 <= v <= 360,
    latitude=lambda v: -90 <= v <= 90,
    longitude=lambda v: -180 <= v <= 180,
    maxradius=lambda v: 0 <= v <= 180,
    maxradiuskm=lambda v: 0 <= v <= 20001.6,
    includedeleted=lambda v: v.strip().lower() in ["true", "false", "only"],
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


@dataclass
# TODO add support for kml
# TODO add support for xml and quakeml
class Query:  # pylint: disable=too-many-instance-attributes
    """Class for managing inputs for queries

    API Docs: https://earthquake.usgs.gov/fdsnws/event/1/

    NOTE: All times use ISO8601 Date/Time format (yyyy-mm-ddThh:mm:ss). UTC is assumed.
    NOTE: Minimum/maximum longitude values may cross the date line at 180 or -180

    Args:
        [Format]
        format: Specify the output format (only "csv", "geojson", and "text" supported for now.
            kml", "quakeml", and "xml" to be added in upcoming release).

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
            returns only deleted events. Values "True" or "False" are typecast to bool.
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
    format: str = field(default=None)
    # Time
    endtime: str = field(default=None)
    starttime: str = field(default=None)
    updatedafter: str = field(default=None)
    # Location - rectangle
    minlatitude: float = field(default=None)
    minlongitude: float = field(default=None)
    maxlatitude: float = field(default=None)
    maxlongitude: float = field(default=None)
    # Location - circle
    latitude: float = field(default=None)
    longitude: float = field(default=None)
    maxradius: float = field(default=None)
    maxradiuskm: float = field(default=None)
    # Other
    catalog: str = field(default=None)
    contributor: str = field(default=None)
    eventid: str = field(default=None)
    includeallmagnitudes: bool = field(default=None)
    includeallorigins: bool = field(default=None)
    includedeleted: str = field(default=None)
    includesuperceded: bool = field(default=None)
    limit: int = field(default=None)
    maxdepth: float = field(default=None)
    maxmagnitude: float = field(default=None)
    mindepth: float = field(default=None)
    minmagnitude: float = field(default=None)
    offset: int = field(default=None)
    orderby: str = field(default=None)
    # Extensions
    alertlevel: str = field(default=None)
    callback: str = field(default=None)
    eventtype: str = field(default=None)
    jsonerror: bool = field(default=None)
    kmlanimated: bool = field(default=None)
    kmlcolorby: str = field(default=None)
    maxcdi: float = field(default=None)
    maxgap: float = field(default=None)
    maxmmi: float = field(default=None)
    maxsig: int = field(default=None)
    mincdi: str = field(default=None)
    minfelt: int = field(default=None)
    mingap: float = field(default=None)
    minsig: int = field(default=None)
    producttype: str = field(default=None)
    productcode: str = field(default=None)
    reviewstatus: str = field(default=None)

    def __post_init__(self):

        # Auto-typecast input values
        bad_values = {}
        for query_field in fields(self):
            name = query_field.name
            val_type = query_field.type
            value = getattr(self, name)

            # Handle generic subtypes, get first parameterised type
            if get_origin(val_type) is not None:
                val_type = get_args(val_type)

            # Typecast values
            if value is not None and not isinstance(value, val_type):
                if not callable(val_type):
                    val_type = val_type[0]
                setattr(self, name, val_type(value))

            # Ensure conditions on parameters are satisfied
            if name in ALLOWED_VALUES and value is not None and not ALLOWED_VALUES[name](value):
                bad_values[name] = value

        if len(bad_values) > 0:
            for name, value in bad_values.items():
                logger.error(f"Invalid value for `{name}`, (got {value})")
            raise AssertionError("Bad values given to query.")

        # TODO remove this artificial guard when better support is added
        if self.format is None:
            self.format = "csv"
        elif self.format not in ["csv", "text", "geojson"]:
            logger.warning(f"Format {self.format} not implemented yet, changing to 'csv'")
            self.format = "csv"

        assert (
            self.maxradiuskm is None or self.maxradius is None
        ), "Only one of `maxradiuskm` and `maxradius` allowed to be specified."

        if self.includesuperceded is not None:
            assert (
                self.eventid is not None
            ), "Parameter `includesuperceded` only works when `eventid` is given."

        if self.includedeleted is not None:
            includedeleted_is_bool = (self.includedeleted.strip().lower()[0] in ['t', 'f'])
            post_type = bool if includedeleted_is_bool else str
            self.includedeleted = post_type(self.includedeleted)

        self._check_format_specific_parameters(["includedeleted"], ["csv", "geojson"])
        self._check_format_specific_parameters(["callback", "jsonerror"], ["geojson"])
        self._check_format_specific_parameters(["kmlcolorby", "kmlanimated"], ["kml"])

    def _check_format_specific_parameters(self, parameters, formats):
        for name in parameters:
            if getattr(self, name) is not None:
                assert (
                    self.format in formats
                ), f"Parameter `{name}` only supported for {', '.join(formats)}."

    def __str__(self):
        out = self.__class__.__name__ + "("
        for key, value in asdict(self).items():
            if value is not None:
                out += "\n" + 4 * " " + f"{key}: {str(value)}"
        out += "\n)"
        return out
