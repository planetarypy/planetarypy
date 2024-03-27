"""Tests for utils module."""

import pytest
import datetime as dt
from pathlib import Path

from planetarypy import utils


## Datetime helpers
@pytest.fixture
def ordinal_datetimes():
    """Return [ordinal_date, ordinal_datetime, ordinal_datetime_with_ms]"""
    return ["2010-110", "2010-110T10:12:14", "2010-110T10:12:14.123000"]


@pytest.fixture
def calendar_datetimes():
    return ["2010-4-20", "2010-04-20T10:12:14", "2010-04-20T10:12:14.123000"]


def test_ordinal_time_to_datetime(ordinal_datetimes):
    ordinal_date, ordinal_datetime, ordinal_datetime_with_ms = ordinal_datetimes
    assert utils.ordinal_time_to_datetime(ordinal_date) == dt.datetime(2010, 4, 20, 0, 0)
    assert utils.ordinal_time_to_datetime(ordinal_datetime) == dt.datetime(2010, 4, 20, 10, 12, 14)
    assert utils.ordinal_time_to_datetime(ordinal_datetime_with_ms) == dt.datetime(2010, 4, 20, 10, 12, 14, 123000)


def test_ordinal_time_to_calendar(ordinal_datetimes):
    ordinal_date, _, _ = ordinal_datetimes
    assert utils.ordinal_time_to_calendar(ordinal_date, with_hours=True) == "2010-04-20T00:00:00"
    assert utils.ordinal_time_to_calendar(ordinal_date) == "2010-04-20"


def test_calendar_to_ordinal_time(calendar_datetimes, ordinal_datetimes):
    calendar_date, calendar_datetime, calendar_datetime_with_ms = calendar_datetimes
    ordinal_date, ordinal_datetime, ordinal_datetime_with_ms = ordinal_datetimes
    assert utils.calendar_to_ordinal_time(calendar_date) == ordinal_date
    assert utils.calendar_to_ordinal_time(calendar_datetime) == ordinal_datetime
    assert utils.calendar_to_ordinal_time(calendar_datetime_with_ms) == ordinal_datetime_with_ms


# File helpers
def test_file_variations():
    fname = "abc.txt"
    extensions = [".cub", ".cal.cub", ".map.cal.cub"]
    variations = utils.file_variations(fname, extensions)
    assert len(variations) == len(extensions)
    assert set(variations) == {Path("abc.cub"), Path("abc.cal.cub"), Path("abc.map.cal.cub")}