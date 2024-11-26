"""Tests for config module."""

import pytest
from pathlib import Path
import tempfile
from planetarypy.config import config, Config, reset_non_urls


def test_config_loading():
    assert isinstance(config.d, dict)
    assert "missions" in config.d


def test_config_missions():
    assert "cassini" in config["missions"]
    assert "iss" in config["missions"]["cassini"]


def test_config_getitem():
    # Test dictionary-like access
    assert config["missions"] is not None
    assert isinstance(config["missions"], dict)


def test_config_missing_key():
    # Test that missing keys return empty string
    assert config.get_value("nonexistent.key") == ""


def test_config_nested_access():
    cassini_config = config["missions"]["cassini"]
    assert isinstance(cassini_config, dict)
    assert "iss" in cassini_config


def test_config_get_value():
    # Test with valid keys
    assert config.get_value("cassini.iss") != ""
    # Test with invalid key
    assert config.get_value("nonexistent.key") == ""
    # Test with full path
    assert config.get_value("missions.cassini.iss") != ""


def test_config_set_value():
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config = Config(Path(tmpdir) / "test_config.toml")
        
        # Initialize the full path structure
        temp_config.tomldoc["missions"] = {"test": {"instrument": {}}}
        temp_config.save()

        # Test setting a new value
        temp_config.set_value("missions.test.instrument.value", "test_value")
        assert temp_config.get_value("test.instrument.value") == "test_value"

        # Test overwriting an existing value
        temp_config.set_value("missions.test.instrument.value", "new_value")
        assert temp_config.get_value("test.instrument.value") == "new_value"


def test_config_list_instruments():
    instruments = config.list_instruments("cassini")
    assert isinstance(instruments, list)
    assert "iss" in instruments


def test_config_get_datalevels():
    datalevels = config.get_datalevels("cassini.iss")
    assert isinstance(datalevels, list)


def test_config_list_indexes():
    indexes = config.list_indexes("cassini.iss")
    assert isinstance(indexes, list)

    # Test with missions prefix
    indexes = config.list_indexes("missions.cassini.iss")
    assert isinstance(indexes, list)


def test_config_storage_root():
    assert config.storage_root.is_dir()
    assert isinstance(config.storage_root, Path)


def test_config_backup():
    backup_name = config.current_backup_name
    assert isinstance(backup_name, Path)
    assert backup_name.name.endswith(".bak")


def test_config_make_backup():
    original_backup = config.current_backup_name
    config.make_backup_copy()
    assert original_backup.exists()


def test_reset_non_urls():
    test_dict = {
        "url": "http://example.com",  # Should be preserved (key contains 'url')
        "regular_key": "value",       # Should be reset
        "nested": {
            "download_url": "http://test.com",  # Should be preserved
            "data_field": "other_value"         # Should be reset
        },
    }

    # Create a deep copy to avoid modifying the original
    import copy
    test_dict_copy = copy.deepcopy(test_dict)
    reset_dict = reset_non_urls(test_dict_copy, "")
    
    # Check that URL fields are preserved
    assert reset_dict["url"] == "http://example.com"
    assert reset_dict["nested"]["download_url"] == "http://test.com"
    
    # Check that non-URL fields are reset
    assert reset_dict["regular_key"] == ""
    assert reset_dict["nested"]["data_field"] == ""
    
    # Verify original dict wasn't modified
    assert test_dict["regular_key"] == "value"
    assert test_dict["nested"]["data_field"] == "other_value"


def test_config_custom_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        custom_path = Path(tmpdir) / "custom_config.toml"
        custom_config = Config(custom_path)
        assert custom_config.path == custom_path
        assert custom_path.exists()


def test_config_missions_property():
    missions = config.missions
    assert isinstance(missions, list)
    assert "cassini" in missions


@pytest.mark.parametrize(
    "mission,expected_instrument",
    [
        ("cassini", "iss"),
        # Add more mission/instrument pairs as needed
    ],
)
def test_config_instruments_for_mission(mission, expected_instrument):
    instruments = config.list_instruments(mission)
    assert expected_instrument in instruments
