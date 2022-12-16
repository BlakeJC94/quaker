from abc import ABC
from dataclasses import dataclass, fields
from datetime import datetime as dt
from inspect import getdoc, getmro
from itertools import product
from typing import Optional, get_args

import pytest

from quaker.core import Query

def assert_query_type_and_value(query, param_name, value):
    param_value = getattr(query, param_name)
    assert param_value == value, f"{param_name = }, {value = }"
    assert isinstance(param_value, query.get_param_type(param_name))


@dataclass
class MockQuery:
    mock_field: Optional[int] = None

    def __post_init__(self):
        type_args = get_args(
            next((f for f in fields(self) if f.name == "mock_field")).type
        )
        self.return_type = next(i for i in type_args if callable(i) and i is not None)

    def _set_return_type(self, return_type):
        self.return_type = return_type

    def get_param_type(self, _):
        return self.return_type


class TestAssertQueryTypeAndValue:
    value = 123

    def test_successful_call(self):
        """assert_query_type_and_value should get attr 'param_name' from query and check the type."""
        mock_query = MockQuery(mock_field=self.value)
        assert_query_type_and_value(mock_query, "mock_field", self.value)

    def test_raise_value_equal_type_unequal(self):

        mock_query = MockQuery(mock_field=self.value)
        mock_query._set_return_type(float)

        with pytest.raises(AssertionError):
            assert_query_type_and_value(mock_query, "mock_field", self.value)

    def test_raise_value_unequal(self):
        mock_query = MockQuery(mock_field=self.value)
        with pytest.raises(AssertionError):
            assert_query_type_and_value(mock_query, "mock_field", 2 * self.value + 1)


class TestQueryValidInputs:
    format = "csv"

    starttime = "2022-08-01"
    endtime = "2022-09-01"
    updatedafter = "2022-07-01"

    minlatitude = 60.0
    minlongitude = 70.0
    maxlatitude = 80.0
    maxlongitude = 90.0

    latitude = 60.0
    longitude = 70.0
    maxradius = 80.0
    maxradiuskm = 85.0

    catalog = "foo"
    contributor = "foo"
    eventid = "id1234"
    includeallmagnitudes = True
    includeallorigins = True
    includedeleted = "true"
    includesuperceded = True
    limit = 300
    maxdepth = 3.1
    maxmagnitude = 7.0
    mindepth = 2.9
    minmagnitude = 6.0
    offset = 600
    orderby = "time"

    alertlevel = "yellow"
    callback = "foo"
    eventtype = "foo"
    jsonerror = True
    kmlanimated = True
    kmlcolorby = "age"
    maxcdi = 12.0
    maxgap = 11.0
    maxmmi = 10.0
    maxsig = 2
    mincdi = 11.0
    minfelt = 10
    mingap = 10.0
    minsig = 1
    producttype = "foo"
    productcode = "foo"
    reviewstatus = "all"

    def test_empty(self):
        """Empty queries should be valid, and have None for each field."""
        query = Query()
        for field in fields(query):
            assert getattr(query, field.name) is None

    @pytest.mark.parametrize(
        "field_names",
        [
            # Format field
            ["format"],
            # Time fields
            [
                "starttime",
                "endtime",
                "updatedafter",
            ],
            # Location (rectangle) fields
            [
                "minlatitude",
                "minlongitude",
                "maxlatitude",
                "maxlongitude",
            ],
            # Location (circle) fields, maxradius
            [
                "latitude",
                "longitude",
                "maxradius",
            ],
            # Location (circle) fields, maxradiuskm
            [
                "latitude",
                "longitude",
                "maxradiuskm",
            ],
            # Other fields, includedeleted
            [
                "catalog",
                "contributor",
                "eventid",
                "includeallmagnitudes",
                "includeallorigins",
                "includedeleted",
                "limit",
                "maxdepth",
                "maxmagnitude",
                "mindepth",
                "minmagnitude",
                "offset",
                "orderby",
            ],
            # Other fields, includesuperceded
            [
                "catalog",
                "contributor",
                "eventid",
                "includeallmagnitudes",
                "includeallorigins",
                "includesuperceded",
                "limit",
                "maxdepth",
                "maxmagnitude",
                "mindepth",
                "minmagnitude",
                "offset",
                "orderby",
            ],
            # Extension fields
            [
                "alertlevel",
                "callback",
                "eventtype",
                "jsonerror",
                "kmlanimated",
                "kmlcolorby",
                "maxcdi",
                "maxgap",
                "maxmmi",
                "maxsig",
                "mincdi",
                "minfelt",
                "mingap",
                "minsig",
                "producttype",
                "productcode",
                "reviewstatus",
            ],
        ],
    )
    def test_params(self, field_names):
        """Ensure inputs are valid."""
        query = Query(**{name: getattr(self, name) for name in field_names})
        for name in field_names:
            assert_query_type_and_value(query, name, getattr(self, name))

    @pytest.mark.parametrize(
        "valid_time",
        [
            "2022-12-16",
            "2022-12-16T02:44:30",
            "2022-12-16T02:44:30+00:00",
        ],
    )
    def test_valid_times(self, valid_time):
        """Ensure time inputs are valid."""
        for attribute in ["starttime", "endtime", "updatedafter"]:
            query = Query(**{attribute: valid_time})
            assert getattr(query, attribute) == valid_time

    @pytest.mark.parametrize(
        "attribute, allowed_values",
        [
            ("orderby", ["time", "time-asc", "magnitude", "magnitude-asc"]),
            ("format", ["csv", "geojson", "text"]),
            ("includedeleted", ["true", "false", "only"]),
            ("alertlevel", ["green", "yellow", "orange", "red"]),
            ("kmlcolorby", ["age", "depth"]),
            ("reviewstatus", ["all", "automatic", "reviewed"]),
        ],
    )
    def test_valid_strings(self, attribute, allowed_values):
        for value in allowed_values:
            query = Query(**{attribute: value})
            assert getattr(query, attribute) == value

        with pytest.raises(ValueError):
            _ = Query(**{attribute: "foo"})

    @pytest.mark.parametrize("invalid_time", ["foo", "01-01-2020"])
    def test_raise_invalid_times(self, invalid_time):
        """ValueError should be raised if a bad time input is given."""
        for attribute in ["starttime", "endtime", "updatedafter"]:
            with pytest.raises(ValueError):
                _ = Query(**{attribute: invalid_time})

    @pytest.mark.parametrize(
        "field_names, invalid_values",
        [
            (["maxcdi", "mincdi"], [-1, 13]),
            (["maxgap", "mingap"], [-1, 361]),
            (["offset"], [0, -1]),
            (["maxradius"], [-0.01, 181]),
            (["maxradiuskm"], [-0.01, 20001.7]),
            (["minlatitude", "minlatitude", "latitude"], [-91, 91]),
            (["minlongitude", "maxlongitude"], [-361, 361]),
            (["longitude"], [-181, 181]),
        ],
    )
    def test_raise_out_of_bounds(self, field_names, invalid_values):
        """ValueError should be raised if a bad time input is given."""
        for attribute, invalid_value in product(field_names, invalid_values):
            with pytest.raises(ValueError):
                _ = Query(**{attribute: invalid_value})

    def test_raise_query_both_radius_params(self):
        """ValueError shoud be raised if attempting to pass in maxradius and maxradiuskm."""
        with pytest.raises(ValueError):
            _ = Query(maxradius=10, maxradiuskm=20)

    def test_raise_query_invalid_latitudes_longitudes(self):
        for attr1, attr2 in [
            ("minlatitude", "maxlatitude"),
            ("minlongitude", "maxlongitude"),
            ("minmagnitude", "maxmagnitude"),
            ("mindepth", "maxdepth"),
        ]:
            with pytest.raises(ValueError):
                _ = Query(**{attr1: 6, attr2: 5})

