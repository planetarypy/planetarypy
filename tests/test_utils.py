"""Tests for utils module."""

import pytest
import datetime as dt
from pathlib import Path

from planetarypy import utils


## Datetime helpers
@pytest.fixture
def nasa_datetimes():
    """Return [nasa_date, nasa_datetime, nasa_datetime_with_ms]"""
    return ["2010-110", "2010-110T10:12:14", "2010-110T10:12:14.123000"]


@pytest.fixture
def iso_datetimes():
    return ["2010-4-20", "2010-04-20T10:12:14", "2010-04-20T10:12:14.123000"]


def test_nasa_time_to_datetime(nasa_datetimes):
    nasa_date, nasa_datetime, nasa_datetime_with_ms = nasa_datetimes
    assert utils.nasa_time_to_datetime(nasa_date) == dt.datetime(2010, 4, 20, 0, 0)
    assert utils.nasa_time_to_datetime(nasa_datetime) == dt.datetime(2010, 4, 20, 10, 12, 14)
    assert utils.nasa_time_to_datetime(nasa_datetime_with_ms) == dt.datetime(2010, 4, 20, 10, 12, 14, 123000)


def test_nasa_time_to_iso(nasa_datetimes):
    nasa_date, _, _ = nasa_datetimes
    assert utils.nasa_time_to_iso(nasa_date, with_hours=True) == "2010-04-20T00:00:00"
    assert utils.nasa_time_to_iso(nasa_date) == "2010-04-20"


def test_iso_to_nasa_time(iso_datetimes, nasa_datetimes):
    iso_date, iso_datetime, iso_datetime_with_ms = iso_datetimes
    nasa_date, nasa_datetime, nasa_datetime_with_ms = nasa_datetimes
    assert utils.iso_to_nasa_time(iso_date) == nasa_date
    assert utils.iso_to_nasa_time(iso_datetime) == nasa_datetime
    assert utils.iso_to_nasa_time(iso_datetime_with_ms) == nasa_datetime_with_ms


# Image processing helpers
def test_file_variations():
    fname = "abc.txt"
    extensions = [".cub", ".cal.cub", ".map.cal.cub"]
    variations = utils.file_variations(fname, extensions)
    assert len(variations) == len(extensions)
    assert set(variations) == {Path("abc.cub"), Path("abc.cal.cub"), Path("abc.map.cal.cub")}