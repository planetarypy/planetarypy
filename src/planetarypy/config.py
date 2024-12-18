__all__ = ["config", "reset_non_urls", "Config"]

import json
import os
import shutil
from collections.abc import Mapping
from functools import reduce
from importlib.resources import files
from pathlib import Path
from typing import Union

import tomlkit


def reset_non_urls(
    source: dict,  # source dictionary
    reset: str = "",  # value to reset non URLs to
) -> dict:
    """Reset all non-URL values in the config file.

    This is useful for copying the private config file with new data items back into the
    source tree for a clean commit.
    """
    for key, value in source.items():
        if isinstance(value, Mapping) and value:
            reset_non_urls(value, reset)
        elif "url" not in key:
            source[key] = reset
    return source


class Config:
    """Manage config stuff.

    The key, value pairs found in the config file become attributes of the
    class instance after initialization.
    At minimum, there should be the `storage_root` attribute for storing data
    for this package.
    """

    # This part enables a config path location override using env PLANETARYPY_CONFIG
    fname = "planetarypy_config.toml"
    # separating fname from fpath so that resource_path below is correct.
    path = Path(os.getenv("PLANETARYPY_CONFIG", Path.home() / f".{fname}"))

    def __init__(self, config_path: str = None):  # str or pathlib.Path
        """Switch to other config file location with `config_path`."""
        if config_path is not None:
            self.path = Path(config_path)
        if not self.path.exists():
            p = files("planetarypy.data").joinpath(self.fname)
            shutil.copy(p, self.path)
        self._read_config()

    def _read_config(self):
        """Read the configfile and store config dict.

        `storage_root` will be stored as attribute.
        """
        self.tomldoc = tomlkit.loads(self.path.read_text())
        if not self.tomldoc["storage_root"]:
            path = Path.home() / "planetarypy_data"
            path.mkdir(exist_ok=True)
            self.tomldoc["storage_root"] = str(path)
            self.storage_root = path
            self.save()
        else:
            self.storage_root = Path(self.tomldoc["storage_root"])

    @property
    def d(self):
        """get the Python dic from"""
        return self.tomldoc

    def __getitem__(self, key: str):
        """Get sub-dictionary by nested key."""
        if not key.startswith("missions"):
            key = "missions." + key
        try:
            return reduce(lambda c, k: c[k], key.split("."), self.d)
        except KeyError:
            return ""

    def get_value(
        self,
        key: str,  # A nested key in dotted format, e.g. cassini.uvis.indexes
    ) -> str:  # Returning empty string if not existing, because Path('') is False which is handy (e.g. in ctx mod.)
        """Get sub-dictionary by nested key."""
        if not key.startswith("missions"):
            key = "missions." + key
        try:
            return reduce(lambda c, k: c[k], key.split("."), self.d)
        except KeyError:
            return ""

    def set_value(
        self,
        nested_key: str,  # A nested key in dotted format, e.g. cassini.uvis.ring_summary
        value: Union[float, str],  # Value for the given key to be stored
        save: bool = True,  # Switch to control writing out to disk
    ):
        """Set value in sub-dic using dotted key."""
        dic = self.tomldoc
        keys = nested_key.split(".")
        for key in keys[:-1]:
            dic = dic[key]
        dic[keys[-1]] = value
        if save:
            self.save()

    def __setitem__(self, nested_key: str, value: Union[float, str]):
        """Set value in sub-dic using dotted key."""
        dic = self.tomldoc
        keys = nested_key.split(".")
        for key in keys[:-1]:
            dic = dic[key]
        dic[keys[-1]] = value
        self.save()

    def save(self):
        """Write the TOML doc to file."""
        self.path.write_text(tomlkit.dumps(self.tomldoc))

    @property
    def missions(self):
        return list(self.d["missions"].keys())

    def list_instruments(self, mission):
        if not mission.startswith("missions"):
            mission = "missions." + mission
        instruments = self.get_value(mission)
        return list(instruments.keys())

    def get_datalevels(
        self,
        mission_instrument,  # mission.instrument code, e.g. mro.hirise
    ):
        """Return configured data levels available for an instrument.

        This currently simply points to the indexes, assuming that everything that has
        an index is also its own datalevel. In case it ever is not, we can add more here.
        """
        return self.list_indexes(mission_instrument)

    def list_indexes(self, instrument):
        """instrument key needs to be <mission>.<instrument>"""
        if not instrument.startswith("missions"):
            instrument = "missions." + instrument
        indexes = self.get_value(instrument + ".indexes")
        return list(indexes)

    def __repr__(self):
        return json.dumps(self.d, indent=2)


config = Config()
