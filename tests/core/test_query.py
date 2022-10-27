from quaker.core import query
from quaker.core.query import is_valid_time


def test_is_valid_time():
    expected_valid = [
        "2022-09-01",
        "2022-09-01 12:34:50",
        "2022-09-01T12:34:50",
        "2022-09-01T12:34:50",
    ]
    expected_invalid = [
        "2022_09_01 12:34",
        "12:34",
    ]

    assert all(is_valid_time(time) for time in expected_valid)
    assert not any(is_valid_time(time) for time in expected_invalid)

