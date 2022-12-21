from abc import ABC
from unittest.mock import patch
from dataclasses import dataclass, fields, asdict, Field
from datetime import datetime as dt
from inspect import getdoc, getmro
from itertools import product
from typing import Optional, get_args

import pytest

from quaker.core.query import (
    Query,
    _BaseQuery,
    _FieldHelper,
    _FieldChecker,
    _CompositeFieldDocumenter,
)


def assert_query_type_and_value(query, field_name, value):
    field_value = getattr(query, field_name)
    assert field_value == value, f"{field_name = }, {value = }"
    assert isinstance(field_value, query.field_types[field_name])


MOCK_QUERY_FIELD_TYPE = int


@dataclass
class _QueryComponentMock(_BaseQuery):
    """A mock dataclass object for testing `_BaseQuery`.

    Args:
        mock_field: A mock field.
        another_mock_field: Another mock field
            with a multiline docstring.
    """

    mock_field: Optional[MOCK_QUERY_FIELD_TYPE] = None
    another_mock_field: Optional[MOCK_QUERY_FIELD_TYPE] = None

    def __post_init__(self):
        super().__post_init__()
        self._set_return_type(MOCK_QUERY_FIELD_TYPE)

    def _set_return_type(self, return_type):
        self.return_type = return_type
        self.field_types = dict(mock_field=self.return_type)


@dataclass
class MockQuery(_CompositeFieldDocumenter, _QueryComponentMock):
    """A mock dataclass object for testing MRO of `_BaseQuery`."""

    @classmethod
    @property
    def __doc__(cls) -> str:
        return cls.generate_doc()

    @classmethod
    @property
    def doc_head(cls) -> str:
        return """DOC HEAD"""

    @classmethod
    @property
    def doc_body(cls) -> str:
        return """DOC BODY"""

    def __post_init__(self):
        super().__post_init__()
        self._mock_query_post_init_called = True

    @classmethod
    @property
    def _expected_doc(cls) -> str:
        doc = "\n\n".join(
            [
                cls.doc_head.removesuffix("\n"),
                cls.doc_body.removesuffix("\n"),
                "Args:",
            ]
        )
        class_doc = getdoc(_QueryComponentMock)
        _, args_doc = class_doc.split("Args:", 1)
        doc = "\n".join([doc, args_doc])
        return doc


class TestAssertQueryTypeAndValue:
    value = 123

    def test_successful_call(self):
        """assert_query_type_and_value should get attr 'field_name' from query and check the type.
        """
        mock_query = _QueryComponentMock(mock_field=self.value)
        assert_query_type_and_value(mock_query, "mock_field", self.value)

    def test_raise_value_equal_type_unequal(self):

        mock_query = _QueryComponentMock(mock_field=self.value)
        mock_query._set_return_type(float)

        with pytest.raises(AssertionError):
            assert_query_type_and_value(mock_query, "mock_field", self.value)

    def test_raise_value_unequal(self):
        mock_query = _QueryComponentMock(mock_field=self.value)
        with pytest.raises(AssertionError):
            assert_query_type_and_value(mock_query, "mock_field", 2 * self.value + 1)

    def test_assert_fields_ordered(self):
        query = _QueryComponentMock(
            mock_field=4,
            another_mock_field=7,
        )
        query.assert_fields_ordered("mock_field", "another_mock_field")

    def test_raise_assert_fields_ordered(self):
        query = _QueryComponentMock(
            mock_field=4,
            another_mock_field=7,
        )
        with pytest.raises(AssertionError):
            query.assert_fields_ordered(
                "another_mock_field",
                "mock_field",
            )

    def test_assert_fields_bounded(self):
        query = _QueryComponentMock(
            mock_field=4,
        )
        min_value, max_value = 3, 5
        query.assert_fields_bounded(["mock_field"], min_value, max_value)
        query.assert_fields_bounded(["another_mock_field"], min_value, max_value)
        query.assert_fields_bounded(["mock_field", "another_mock_field"], min_value, max_value)

    @pytest.mark.parametrize(
        "min_value, max_value",
        [
            (5, 6),
            (5, None),
            (1, 2),
            (None, 2),
        ],
    )
    def test_raise_assert_fields_bounded(self, min_value, max_value):
        query = _QueryComponentMock(
            mock_field=4,
        )
        with pytest.raises(AssertionError):
            query.assert_fields_bounded(["another_mock_field", "mock_field"], min_value, max_value)

    def test_assert_fields_mutually_exclusive(self):
        query = _QueryComponentMock(
            mock_field=4,
        )
        query.assert_fields_mutually_exclusive(['mock_field', 'another_mock_field'])

    def test_raise_assert_fields_mutually_exclusive(self):
        query = _QueryComponentMock(
            mock_field=4,
            another_mock_field=7,
        )
        with pytest.raises(AssertionError):
            query.assert_fields_mutually_exclusive(['mock_field', 'another_mock_field'])

    def test_assert_field_allowed_values(self):
        query = _QueryComponentMock(
            mock_field=4,
        )
        query.assert_field_allowed_values('mock_field', [4])

    def test_raise_assert_field_allowed_values(self):
        query = _QueryComponentMock(
            mock_field=4,
            another_mock_field=7,
        )
        with pytest.raises(AssertionError):
            query.assert_field_allowed_values('mock_field', [5])


class TestBaseQuery:
    def test_docs(self):
        query = MockQuery()
        # pylint: disable=protected-access
        assert getdoc(query) == query._expected_doc

    def test_name(self):
        query = _QueryComponentMock()
        assert query.name == "component (mock)"

    def test_post_init(self):
        with patch("quaker.core.query._BaseQuery.__post_init__") as mock_post_init:
            query = MockQuery()
            mock_post_init.assert_called()
            assert query._mock_query_post_init_called

    def test_fields(self):
        query = _QueryComponentMock()
        query_fields = query.fields
        assert list(query_fields.keys()) == ["mock_field", "another_mock_field"]
        for k in query_fields:
            assert isinstance(query_fields.get(k), Field)

    def test_field_docs(self):
        query = _QueryComponentMock()
        field_docs = query.field_docs
        expected_items = [
            ("mock_field", "A mock field."),
            ("another_mock_field", "Another mock field with a multiline docstring."),
        ]
        # pylint: disable=invalid-name,invalid-name,invalid-name,invalid-name
        for (k1, v1), (k2, v2) in zip(field_docs.items(), expected_items):
            assert k1 == k2
            assert v1 == v2

    def test_field_types(self):
        query = _QueryComponentMock()
        field_types = query.field_types
        assert list(field_types.keys()) == ["mock_field"]
        for k in field_types:
            assert field_types.get(k) == int


class TestQuery:
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

    def test_asdict(self):
        query_input = dict(
            starttime=self.starttime,
            endtime=self.endtime,
            updatedafter=self.updatedafter,
            minlatitude=self.minlatitude,
            minlongitude=self.minlongitude,
            maxlatitude=self.maxlatitude,
            maxlongitude=self.maxlongitude,
        )
        query = Query(**query_input)
        assert {k: v for k, v in asdict(query).items() if v is not None} == query_input

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
    def test_fields(self, field_names):
        """Ensure inputs are valid."""
        query = Query(**{name: getattr(self, name) for name in field_names})
        for name in field_names:
            assert_query_type_and_value(query, name, getattr(self, name))

        with patch("quaker.core.query._BaseQuery.__post_init__") as mock_post_init:
            query = Query(**{name: getattr(self, name) for name in field_names})
            mock_post_init.assert_called()

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

        with pytest.raises(AssertionError):
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
            with pytest.raises(AssertionError):
                _ = Query(**{attribute: invalid_value})

    def test_raise_query_both_radius_fields(self):
        """ValueError shoud be raised if attempting to pass in maxradius and maxradiuskm."""
        with pytest.raises(AssertionError):
            _ = Query(maxradius=10, maxradiuskm=20)

    def test_raise_query_invalid_latitudes_longitudes(self):
        for attr1, attr2 in [
            ("minlatitude", "maxlatitude"),
            ("minlongitude", "maxlongitude"),
            ("minmagnitude", "maxmagnitude"),
            ("mindepth", "maxdepth"),
        ]:
            with pytest.raises(AssertionError):
                _ = Query(**{attr1: 6, attr2: 5})
