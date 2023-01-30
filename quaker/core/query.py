"""Classes and methods for representation of queries."""
from abc import ABC, abstractproperty
import re
from dataclasses import dataclass, fields, asdict, Field
from datetime import datetime as dt
from inspect import getdoc, getmro
from typing import Optional, get_args, Any, List, Dict


class _FieldHelper:
    """Mixin for generating metadata for a dataclass."""

    @classmethod
    @property
    def fields(cls) -> Dict[str, Field]:
        return {f.name: f for f in fields(cls)}

    @classmethod
    @property
    def field_docs(cls):
        _, doc = cls.__doc__.split("Args:", 1)
        doc = doc.strip().replace("\n" + " " * 12, " ")  # TODO replace this with regex

        field_docs = {}
        field_names = list(cls.fields.keys())
        for line in doc.split("\n"):
            for name in field_names:
                if name + ":" in line:
                    field_names.remove(name)
                    _, field_doc = line.split(":", 1)
                    field_docs[name] = field_doc.strip()
                    break

        return field_docs

    @classmethod
    @property
    def field_types(cls):
        field_types = {}
        for name, f in cls.fields.items():
            if callable(f.type) and not hasattr(f.type, "__args__"):
                f_type = f.type
            else:
                f_types = get_args(f.type)
                f_type = next(t for t in f_types if t is not None and callable(t))
            field_types[name] = f_type

        return field_types


class _FieldChecker:
    def assert_fields_ordered(self, min_field_name, max_field_name):
        min_field_value = getattr(self, min_field_name)
        max_field_value = getattr(self, max_field_name)
        if min_field_value is not None and max_field_value is not None:
            assert min_field_value < max_field_value, (
                f"{min_field_name} ({min_field_value}) is larger than "
                f"{max_field_name} ({max_field_value})."
            )

    def assert_fields_bounded(self, field_names, min_value=None, max_value=None):
        for field_name in field_names:
            field_value = getattr(self, field_name)
            if field_value is not None:
                assert (
                    min_value is None or min_value <= field_value
                ), f"{field_name} is less than {min_value}."
                assert (
                    max_value is None or field_value <= max_value
                ), f"{field_name} is greater than {max_value}."

    def assert_fields_mutually_exclusive(self, field_names):
        n_values_not_none = sum(
            int(getattr(self, field_name) is not None) for field_name in field_names
        )
        assert n_values_not_none <= 1, f"Only one of {field_names} can be accepted."

    def assert_field_allowed_values(self, field_name, allowed_values):
        field_value = getattr(self, field_name)
        assert field_value is None or field_value in allowed_values, (
            f"Invalid {field_name} ({field_value}), " f"must be one of {allowed_values}."
        )


@dataclass
class _BaseQuery(_FieldHelper, _FieldChecker):
    """Base dataclass used to resolve multiple init and post-init calls in classes that inherit
    from multiple dataclasses.

    Each component parent dataclass should inherit from this class. If component needs a
    __post_init__, it should call super().__post_init__ to ensure that the calls are chained.
    """

    def __post_init__(self):
        """Auto-typecast fields as their appropriate types."""
        for field_name in self.fields:
            value = getattr(self, field_name)
            if value is None:
                continue
            field_type = self.field_types.get(field_name)
            if not isinstance(value, field_type) and callable(field_type):
                setattr(self, field_name, field_type(value))

    @classmethod
    @property
    def name(cls) -> str:
        name = cls.__name__.removeprefix("_").removeprefix("Query")
        name = re.sub(r"(\w)([A-Z])", r"\1 \2", name)
        name_components = name.split(" ")
        name = name_components[0] + " (" + " ".join(name_components[1:]) + ")"
        return name.lower().removesuffix(" ()")

    def __str__(self):
        out = self.__class__.__name__ + "("
        for key, value in asdict(self).items():
            if value is not None:
                out += "\n" + 4 * " " + f"{key}: {str(value)}"
        out += "\n)"
        return out


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
                raise ValueError(f"Invalid time given (received {time_value})") from exc


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
        self.assert_fields_bounded(["minlatitude", "maxlatitude"], -90, 90)
        self.assert_fields_bounded(["minlongitude", "maxlongitude"], -360, 360)
        self.assert_fields_ordered("minlatitude", "maxlatitude")
        self.assert_fields_ordered("minlongitude", "maxlongitude")


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
        self.assert_fields_mutually_exclusive(["maxradius", "maxradiuskm"])
        self.assert_fields_bounded(["maxradius"], 0, 180)
        self.assert_fields_bounded(["maxradiuskm"], 0, 20001.6)
        self.assert_fields_bounded(["latitude"], -90, 90)
        self.assert_fields_bounded(["longitude"], -180, 180)


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
        self.assert_fields_mutually_exclusive(["includedeleted", "includesuperceded"])
        self.assert_field_allowed_values(
            "orderby", ["time", "time-asc", "magnitude", "magnitude-asc"]
        )
        self.assert_field_allowed_values("includedeleted", ["true", "false", "only"])
        self.assert_fields_ordered("minmagnitude", "maxmagnitude")
        self.assert_fields_ordered("mindepth", "maxdepth")
        self.assert_fields_bounded(["minmagnitude", "maxmagnitude"], 0, 12)
        self.assert_fields_bounded(["offset"], 1, None)
        self.assert_fields_bounded(["limit"], 0, None)


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
        self.assert_field_allowed_values("alertlevel", ["green", "yellow", "orange", "red"])
        self.assert_field_allowed_values("kmlcolorby", ["age", "depth"])
        self.assert_field_allowed_values("reviewstatus", ["all", "automatic", "reviewed"])

        self.assert_fields_bounded(["mingap", "maxgap"], 0, 360)
        self.assert_fields_bounded(["mincdi", "maxcdi"], 0, 12)

        self.assert_fields_ordered("mingap", "maxgap")
        self.assert_fields_ordered("mincdi", "maxcdi")


@dataclass
class _QueryFormat(_BaseQuery):
    """Class for managing inputs for queries

    Args:
        [Format]
        format: Specify the output format (one of "csv", "geojson", "text", kml", "quakeml", or
            "xml").
    """

    format: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        self.format = self.format
        self.assert_field_allowed_values(
            "format", ["csv", "text", "geojson", "xml", "quakeml", "xml"]
        )


# TODO usage docs
class _CompositeFieldDocumenter(ABC):
    @classmethod
    @abstractproperty
    def doc_head(cls) -> str:
        return ""

    @classmethod
    @abstractproperty
    def doc_body(cls) -> str:
        return ""

    @classmethod
    def generate_doc(cls) -> str:
        doc = "\n\n".join(
            [
                cls.doc_head.removesuffix("\n"),
                cls.doc_body.removesuffix("\n"),
                "Args:",
            ]
        )
        for class_name in cls.component_classes:
            class_doc = getdoc(class_name)
            _, args_doc = class_doc.split("Args:", 1)
            doc = "\n".join([doc, args_doc])
        return doc

    @classmethod
    @property
    def component_classes(cls) -> List[Any]:
        return [
            class_name
            for class_name in getmro(cls)
            if class_name
            not in [
                cls,
                _BaseQuery,
                ABC,
                object,
                _FieldHelper,
                _FieldChecker,
                _CompositeFieldDocumenter,
            ]
        ]


@dataclass
class Query(
    _CompositeFieldDocumenter,
    _QueryFormat,
    _QueryTime,
    _QueryLocationRectangle,
    _QueryLocationCircle,
    _QueryOther,
    _QueryExtensions,
):
    """Class for managing inputs for queries (**documentation dynamically generated below**)."""

    @classmethod
    @property
    def __doc__(cls):
        return cls.generate_doc()

    @classmethod
    @property
    def doc_head(cls):
        return """Class for managing inputs for queries."""

    @classmethod
    @property
    def doc_body(cls):
        return """API Docs: https://earthquake.usgs.gov/fdsnws/event/1/

        NOTE: All times use ISO8601 Date/Time format (yyyy-mm-ddThh:mm:ss). UTC is assumed.
        NOTE: Minimum/maximum longitude values may cross the date line at 180 or -180
        """

    def dict(self, include_nones: bool = False) -> Dict[str, Any]:
        """Convert the query object into a dictionary.

        Args:
            include_nones: Whether to include keys that have `None` value.
        """
        query_dict = asdict(self)
        if include_nones:
            return query_dict
        return {k: v for k, v in query_dict.items() if v is not None}
