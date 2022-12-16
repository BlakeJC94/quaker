"""Classes and methods for representation of queries."""
from abc import ABC
from dataclasses import dataclass, fields, asdict
from datetime import datetime as dt
from inspect import getdoc, getmro
from typing import Optional, get_args


@dataclass
class _BaseQuery(ABC):
    """Base dataclass used to resolve multiple init and post-init calls in classes that inherit
    from multiple dataclasses.

    Each component parent dataclass should inherit from this class. If component needs a
    __post_init__, it should call super().__post_init__ to ensure that the calls are chained.
    """

    def __post_init__(self):
        """Auto-typecast fields as their appropriate types."""
        for param in fields(self):
            param_value = getattr(self, param.name)
            if param_value is None:
                continue
            param_type = self.get_param_type(param.name)
            if not isinstance(param_value, param_type):
                setattr(self, param.name, param_type(param_value))

    def get_param_type(self, name):
        param = next(i for i in fields(self) if i.name == name)
        if callable(param.type) and not hasattr(param.type, "__args__"):
            return param.type

        param_types = get_args(param.type)
        return next(t for t in param_types if t is not None and callable(t))

    def check_fields_ordered(self, min_field_name, max_field_name):
        min_field_value = getattr(self, min_field_name)
        max_field_value = getattr(self, max_field_name)
        if (
            all(v is not None for v in [min_field_value, max_field_value])
            and min_field_value > max_field_value
        ):
            raise ValueError(
                f"{min_field_name} ({min_field_value}) is larger than "
                f"{max_field_name} ({max_field_value})."
            )

    def check_fields_bounded(self, field_names, min_value=None, max_value=None):
        for field_name in field_names:
            field_value = getattr(self, field_name)
            if field_value is not None:
                if min_value is not None and field_value < min_value:
                    raise ValueError(f"{field_name} is less than {min_value}.")

                if max_value is not None and field_value > max_value:
                    raise ValueError(f"{field_name} is greater than {max_value}.")

    def check_fields_mutually_exclusive(self, field_names):
        n_values_not_none = sum(
            int(getattr(self, field_name) is not None) for field_name in field_names
        )
        if n_values_not_none > 1:
            raise ValueError(f"Only one of {field_names} can be accepted.")

    def check_field_allowed_values(self, field_name, allowed_values):
        field_value = getattr(self, field_name)
        if field_value is not None and field_value not in allowed_values:
            raise ValueError(
                f"Invalid {field_name} ({field_value}), "
                f"must be one of {allowed_values}."
            )


@dataclass
class _QueryTime(_BaseQuery):
    """Query parameters.

    Args:
        [Time]
        endtime: Limit to events on or before the specified end time.
        starttime: Limit to events on or after the specified start time.
        updatedafter: Limit to events updated after the specified time.
    """

    starttime: Optional[str] = None
    endtime: Optional[str] = None
    updatedafter: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        for time_field in ["starttime", "endtime", "updatedafter"]:
            self.check_time_field_is_valid(time_field)

    def check_time_field_is_valid(self, field_name):
        time_value = getattr(self, field_name)
        if time_value is not None:
            try:
                dt.fromisoformat(time_value)
            except Exception as exc:
                raise ValueError(f"Invalid time given for {time_value}") from exc


@dataclass
class _QueryLocationRectangle(_BaseQuery):
    """Query parameters for rectangle location.

    Args:
        [Location - rectangle]
        minlatitude: Limit to events with a latitude larger than the specified minimum [-90, 90).
        minlongitude: Limit to events with a longitude larger than the specified minimum [-360,
            360).
        maxlatitude: Limit to events with a latitude smaller than the specified maximum [-90, 90).
        maxlongitude: Limit to events with a longitude smaller than the specified maximum [-360,
            360).
    """

    minlatitude: Optional[float] = None
    minlongitude: Optional[float] = None
    maxlatitude: Optional[float] = None
    maxlongitude: Optional[float] = None

    def __post_init__(self):
        super().__post_init__()
        self.check_fields_bounded(["minlatitude", "maxlatitude"], -90, 90)
        self.check_fields_bounded(["minlongitude", "maxlongitude"], -360, 360)
        self.check_fields_ordered("minlatitude", "maxlatitude")
        self.check_fields_ordered("minlongitude", "maxlongitude")


@dataclass
class _QueryLocationCircle(_BaseQuery):
    """Query parameters for location (circle).

    Args:
        [Location - circle]
        latitude: Specify the latitude to be used for a radius search [-90, 90].
        longitude: Specify the longitude to be used for a radius search [-180, 180].
        maxradius: Limit to events within the specified maximum number of degrees from the
            geographic point defined by the latitude and longitude parameters [0, 180].
        maxradiuskm: Limit to events within the specified maximum number of kilometers from the
            geographic point defined by the latitude and longitude parameters [0, 20001.6].
    """

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    maxradius: Optional[float] = None
    maxradiuskm: Optional[float] = None

    def __post_init__(self):
        super().__post_init__()
        self.check_fields_mutually_exclusive(["maxradius", "maxradiuskm"])
        self.check_fields_bounded(["maxradius"], 0, 180)
        self.check_fields_bounded(["maxradiuskm"], 0, 20001.6)
        self.check_fields_bounded(["latitude"], -90, 90)
        self.check_fields_bounded(["longitude"], -180, 180)


@dataclass
class _QueryOther(_BaseQuery):
    """Query parameters for other.

    Args:
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
    """

    catalog: Optional[str] = None
    contributor: Optional[str] = None
    eventid: Optional[str] = None
    includeallmagnitudes: Optional[bool] = None
    includeallorigins: Optional[bool] = None
    includedeleted: Optional[str] = None
    includesuperceded: Optional[bool] = None
    limit: Optional[int] = None
    maxdepth: Optional[float] = None
    maxmagnitude: Optional[float] = None
    mindepth: Optional[float] = None
    minmagnitude: Optional[float] = None
    offset: Optional[int] = None
    orderby: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.check_fields_mutually_exclusive(["includedeleted", "includesuperceded"])
        self.check_field_allowed_values(
            "orderby", ["time", "time-asc", "magnitude", "magnitude-asc"]
        )
        self.check_field_allowed_values("includedeleted", ["true", "false", "only"])
        self.check_fields_ordered("minmagnitude", "maxmagnitude")
        self.check_fields_ordered("mindepth", "maxdepth")
        self.check_fields_bounded(["minmagnitude", "maxmagnitude"], 0, 12)
        self.check_fields_bounded(["offset"], 1, None)


@dataclass
class _QueryExtensions(_BaseQuery):
    """Query parameters for other.

    Args:
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

    alertlevel: Optional[str] = None
    callback: Optional[str] = None
    eventtype: Optional[str] = None
    jsonerror: Optional[bool] = None
    kmlanimated: Optional[bool] = None
    kmlcolorby: Optional[str] = None
    maxcdi: Optional[float] = None
    maxgap: Optional[float] = None
    maxmmi: Optional[float] = None
    maxsig: Optional[int] = None
    mincdi: Optional[float] = None
    minfelt: Optional[int] = None
    mingap: Optional[float] = None
    minsig: Optional[int] = None
    producttype: Optional[str] = None
    productcode: Optional[str] = None
    reviewstatus: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.check_field_allowed_values(
            "alertlevel", ["green", "yellow", "orange", "red"]
        )
        self.check_field_allowed_values("kmlcolorby", ["age", "depth"])
        self.check_field_allowed_values(
            "reviewstatus", ["all", "automatic", "reviewed"]
        )

        self.check_fields_bounded(["mingap", "maxgap"], 0, 360)
        self.check_fields_bounded(["mincdi", "maxcdi"], 0, 12)

        self.check_fields_ordered("mingap", "maxgap")
        self.check_fields_ordered("mincdi", "maxcdi")


@dataclass
class _QueryFormat(_BaseQuery):
    """Class for managing inputs for queries

    Args:
        [Format]
        format: Specify the output format (only "csv", "geojson", and "text" supported for now.
            kml", "quakeml", and "xml" to be added in upcoming release).
    """
    format: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        # TODO Add 'xml', 'quakeml', 'kml'
        self.check_field_allowed_values("format", ["csv", "geojson", "text"])

@dataclass
class Query(
    _QueryFormat,
    _QueryTime,
    _QueryLocationRectangle,
    _QueryLocationCircle,
    _QueryOther,
    _QueryExtensions,
):
    """Class for managing inputs for queries

    API Docs: https://earthquake.usgs.gov/fdsnws/event/1/

    NOTE: All times use ISO8601 Date/Time format (yyyy-mm-ddThh:mm:ss). UTC is assumed.
    NOTE: Minimum/maximum longitude values may cross the date line at 180 or -180
    """

    def __str__(self):
        out = self.__class__.__name__ + "("
        for key, value in asdict(self).items():
            if value is not None:
                out += "\n" + 4 * " " + f"{key}: {str(value)}"
        out += "\n)"
        return out

    @classmethod
    def get_parent_classes(cls):
        return [
            class_name for class_name in getmro(cls)
            if class_name not in [Query, _BaseQuery, ABC, object]
        ]

def _assemble_docs(query_class):
    doc = "\n\n".join([getdoc(query_class),"Args:"])
    for class_name in query_class.get_parent_classes():
        class_doc = getdoc(class_name)
        _, args_doc = class_doc.split("Args:", 1)
        doc = "\n".join([doc, args_doc])

    return doc

# TODO Is there a neater way of doing this within the class?
Query.__doc__ = _assemble_docs(Query)


