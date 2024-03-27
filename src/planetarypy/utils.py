"""General utility functions for planetarypy."""

__all__ = [
    "logger",
    "nasa_date_format",
    "nasa_dt_format",
    "nasa_dt_format_with_ms",
    "iso_date_format",
    "iso_dt_format",
    "iso_dt_format_with_ms",
    "nasa_time_to_datetime",
    "nasa_time_to_iso",
    "iso_to_nasa_time",
    "iso_to_nasa_datetime",
    "replace_all_nasa_times",
    "parse_http_date",
    "get_remote_timestamp",
    "check_url_exists",
    "url_retrieve",
    "have_internet",
    "height_from_shadow",
    "file_variations",
]


import datetime as dt
import email.utils as eut
import http.client as httplib
import logging
from math import radians, tan
from pathlib import Path
from typing import Union
from urllib.request import urlopen

import requests
from requests.auth import HTTPBasicAuth
from tqdm.auto import tqdm

import pandas as pd

logger = logging.getLogger(__name__)

# Define the different format strings these utils convert from and to.
# Identifiers with xxx_dt_format_xxx signify a full datetime format as
# compared to dates only.
nasa_date_format = "%Y-%j"
nasa_dt_format = nasa_date_format + "T%H:%M:%S"
nasa_dt_format_with_ms = nasa_dt_format + ".%f"
iso_date_format = "%Y-%m-%d"
iso_dt_format = iso_date_format + "T%H:%M:%S"
iso_dt_format_with_ms = iso_dt_format + ".%f"


## NASA date to datetime and ISO
# What we call NASA data, is the often used YYYY-JJJ based format in the
# Planetary Data System identifying dates via the running number of the day
# in the year, e.g. "2010-240".
def _nasa_date_to_datetime(datestr: str) -> dt.datetime:
    """Convert date string of the form Y-j to datetime."""
    return dt.datetime.strptime(datestr, nasa_date_format)


def _nasa_datetime_to_datetime(datetimestr: str) -> dt.datetime:
    """Convert datetime string of the form Y-jTH:M:S to datetime."""
    return dt.datetime.strptime(datetimestr, nasa_dt_format)


def _nasa_datetimems_to_datetime(datetimestr: str) -> dt.datetime:
    """Convert datetimestr of the form Y-jTH:M:S.xxx to datetime."""
    return dt.datetime.strptime(datetimestr, nasa_dt_format_with_ms)


def nasa_time_to_datetime(inputstr) -> dt.datetime:
    """
    Convert NASA PDS datestrings with day_of_year (jjj) into datetimes.
    
    Parameters
    ----------
    inputstr : str
        Datestring of the form yyyy-jjj(THH:MM:SS)(.ffffff)
    """
    try:
        return _nasa_datetime_to_datetime(inputstr)
    except ValueError:
        try:
            return _nasa_date_to_datetime(inputstr)
        except ValueError:
            return _nasa_datetimems_to_datetime(inputstr)


def nasa_time_to_iso(inputstr: str, with_hours: bool = False) -> str:
    """
    Convert NASA datetime format to ISO format.

    E.g., 2010-110(T10:12:14)" -> 2010-04-20(T10:12:14)

    Parameters
    ----------
    inputstr : str
        Datestring of the form yyyy-jjj(THH:MM:SS)(.ffffff)
    with_hours : bool
        Return ISO with hours or not. Default is False.
    """
    has_hours = False
    # check if input has hours
    try:
        res = _nasa_date_to_datetime(inputstr)
    except ValueError:
        has_hours = True
    time = nasa_time_to_datetime(inputstr)
    if has_hours or with_hours is True:
        return time.isoformat()
    else:
        return time.strftime(iso_date_format)


def iso_to_nasa_time(inputstr: str) -> str:
    """
    Convert ISO datetime format to NASA datetime format.

    E.g., 2010-04-20(T10:12:14) -> 2010-110(T10:12:14)

    Parameters
    ----------
    inputstr : str
        Datestring of the form yyyy-mm-dd(THH:MM:SS)(.ffffff)
    """
    try:
        date = dt.datetime.strptime(inputstr, iso_date_format)
    except ValueError:
        try:
            date = dt.datetime.strptime(inputstr, iso_dt_format)
        except ValueError:
            date = dt.datetime.strptime(inputstr, iso_dt_format_with_ms)
            return date.strftime(nasa_dt_format_with_ms)
        else:
            return date.strftime(nasa_dt_format)
    else:
        return date.strftime(nasa_date_format)


def iso_to_nasa_datetime(dtimestr: str) -> str:
    """
    Convert ISO datetime format to NASA datetime format.

    E.g., 2010-04-20(T10:12:14) -> 2010-110(T10:12:14)

    Parameters
    ----------
    dtimestr : str
        Datestring of the form yyyy-mm-dd(THH:MM:SS)(.ffffff)
    """
    try:
        dtimestr.split(".")[1]
    except IndexError:
        source_format = iso_dt_format
        target_format = nasa_dt_format
    else:
        source_format = iso_dt_format_with_ms
        target_format = nasa_dt_format_with_ms
    date = dt.datetime.strptime(dtimestr, source_format)
    return date.strftime(target_format)


def replace_all_nasa_times(df: pd.DataFrame):
    """
    Convert all detected NASA time columns in df to ISO format in place.

    All columns with "TIME" in the name will be converted and changes will be 
    implemented on incoming dataframe in place (no returned dataframe)!
    """
    for col in [col for col in df.columns if "TIME" in col]:
        if "T" in df[col].iloc[0]:
            df[col] = pd.to_datetime(df[col].map(nasa_time_to_iso))


## Network and file handling
def parse_http_date(http_datestr: str) -> dt.datetime:
    """Parse date string retrieved via urllib.request."""
    return dt.datetime(*eut.parsedate(http_datestr)[:6])


def get_remote_timestamp(url: str) -> dt.datetime:
    """
    Return the timestamp (last-modified) of a remote file at a URL.

    Useful for checking if there's an updated file available.
    """
    with urlopen(str(url), timeout=10) as conn:
        t = parse_http_date(conn.headers["last-modified"])
    return t


def check_url_exists(url):
    """Check if a URL exists."""
    response = requests.head(url)
    if response.status_code < 400:
        return True
    else:
        return False


def url_retrieve(url: str, 
                 outfile: str,
                 chunk_size: int = 4096,  
                 user: str = None,  
                 passwd: str = None,
                 ):
    """
    Downloads a file from url to outfile.

    Improved urlretrieve with progressbar, timeout and chunker.
    This downloader has built-in progress bar using tqdm and the `requests`
    package. Improves on standard `urllib` by adding time-out capability.

    Testing different chunk_sizes, 128 was usually fastest, YMMV.

    Inspired by https://stackoverflow.com/a/61575758/680232

    Parameters
    ----------
    url : str
        The URL to download
    outfile : str
        The path where to store the downloaded file.
    chunk_size : int
        def chunk size for the request.iter_content call
    user : str
        if provided, create HTTPBasicAuth object
    passwd : str
        if provided, create HTTPBasicAuth object
    """
    if user:
        auth = HTTPBasicAuth(user, passwd)
    else:
        auth = None
    R = requests.get(url, stream=True, allow_redirects=True, auth=auth)
    if R.status_code != 200:
        raise ConnectionError(f"Could not download {url}\nError code: {R.status_code}")
    with tqdm.wrapattr(
        open(outfile, "wb"),
        "write",
        miniters=1,
        total=int(R.headers.get("content-length", 0)),
        desc=str(Path(outfile).name),
    ) as fd:
        for chunk in R.iter_content(chunk_size=chunk_size):
            fd.write(chunk)


def have_internet():
    """
    Fast way to check for active internet connection.

    From https://stackoverflow.com/a/29854274/680232
    """
    conn = httplib.HTTPConnection("www.google.com", timeout=5)
    try:
        conn.request("HEAD", "/")
        return True
    except Exception:
        return False
    finally:
        conn.close()


## Image processing helpers
def height_from_shadow(shadow_in_pixels: float, sun_elev: float) -> float:
    """
    Calculate height of an object from its shadow length.

    Note, that your image might have been binned.
    You need to correct `shadow_in_pixels` for that.

    Parameters
    ----------
    shadow_in_pixels : float
        Measured length of shadow in pixels.
    sun_elev : float
        Angle of sun over horizon in degrees.
    """
    return tan(radians(sun_elev)) * shadow_in_pixels


def file_variations(filename: Union[str, Path], extensions: list) -> list:
    """
    Return list of variations of a file name based on possible extensions.

    Generate a list of variations on a filename by replacing the extension with
    the provided list.

    Adapted from T. Olsens `file_variations of the pysis module for using pathlib.

    Parameters
    ----------
    filename : str
        The original filename to use as a base.
    extensions : list
        List of extensions to use for variations.
    """
    return [Path(filename).with_suffix(extension) for extension in extensions]
