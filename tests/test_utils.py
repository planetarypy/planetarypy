"""Tests for utils module."""

from pathlib import Path
import pytest

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

def test_file_variations_with_path():
    fname = Path("/path/to/abc.txt")
    extensions = [".cub", ".cal.cub"]
    variations = utils.file_variations(fname, extensions)
    assert len(variations) == len(extensions)
    assert set(variations) == {
        Path("/path/to/abc.cub"),
        Path("/path/to/abc.cal.cub"),
    }

def test_file_variations_empty_extensions():
    fname = "abc.txt"
    extensions = []
    variations = utils.file_variations(fname, extensions)
    assert len(variations) == 0
    assert variations == []

def test_file_variations_invalid_extension():
    fname = "abc.txt"
    extensions = ["cub"]  # Missing dot prefix
    with pytest.raises(ValueError):
        utils.file_variations(fname, extensions)

def test_file_variations_non_list():
    fname = "abc.txt"
    invalid_inputs = [
        None,
        42,
        {"ext": ".cub"},
        ".cub",  # Single string instead of list
    ]
    for invalid_input in invalid_inputs:
        with pytest.raises((TypeError, AttributeError)):
            utils.file_variations(fname, invalid_input)
