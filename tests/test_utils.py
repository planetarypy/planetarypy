"""Tests for utils module."""

from pathlib import Path

from planetarypy import utils


# File helpers
def test_file_variations():
    fname = "abc.txt"
    extensions = [".cub", ".cal.cub", ".map.cal.cub"]
    variations = utils.file_variations(fname, extensions)
    assert len(variations) == len(extensions)
    assert set(variations) == {
        Path("abc.cub"),
        Path("abc.cal.cub"),
        Path("abc.map.cal.cub"),
    }
