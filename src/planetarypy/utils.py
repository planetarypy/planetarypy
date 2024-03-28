"""General utility functions for planetarypy."""

__all__ = [
    "logger",
    "ordinal_date_format",
    "ordinal_dt_format",
    "ordinal_dt_format_with_ms",
    "calendar_date_format",
    "calendar_dt_format",
    "calendar_dt_format_with_ms",
    "ordinal_time_to_datetime",
    "ordinal_time_to_calendar",
    "calendar_to_ordinal_time",
    "calendar_to_ordinal_datetime",
    "replace_all_ordinal_times",
    "parse_http_date",
    "get_remote_timestamp",
    "check_url_exists",
    "url_retrieve",
    "have_internet",
    "file_variations",
]

import datetime as dt
import email.utils as eut
import http.client as httplib
import logging
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
ordinal_date_format = "%Y-%j"
ordinal_dt_format = ordinal_date_format + "T%H:%M:%S"
ordinal_dt_format_with_ms = ordinal_dt_format + ".%f"
calendar_date_format = "%Y-%m-%d"
calendar_dt_format = calendar_date_format + "T%H:%M:%S"
calendar_dt_format_with_ms = calendar_dt_format + ".%f"


## Ordinal date to datetime and calendar
# What we call ordinal dates, are the often used yyyy-jjj based format in the
# Planetary Data System identifying dates via the running number of the day
# in the year, e.g. "2010-240".
def _ordinal_date_to_datetime(date: str) -> dt.datetime:
    """Convert date string of the form yyyy-jjj to datetime."""
    return dt.datetime.strptime(date, ordinal_date_format)


def _ordinal_datetime_to_datetime(datetime: str) -> dt.datetime:
    """Convert datetime string of the form yyyy-jjjTH:M:S to datetime."""
    return dt.datetime.strptime(datetime, ordinal_dt_format)


def _ordinal_datetimems_to_datetime(datetime: str) -> dt.datetime:
    """Convert datetimestr of the form yyyy-jjjTH:M:S.xxx to datetime."""
    return dt.datetime.strptime(datetime, ordinal_dt_format_with_ms)


def ordinal_time_to_datetime(ordinal_datetime: str) -> dt.datetime:
    """
    Convert ordinal (day-of year) datestrings into datetimes.
    
    Parameters
    ----------
    ordinal_datetime : str
        Datetime string of the form yyyy-jjj(THH:MM:SS)(.ffffff)
    """
    try:
        return _ordinal_datetime_to_datetime(ordinal_datetime)
    except ValueError:
        try:
            return _ordinal_date_to_datetime(ordinal_datetime)
        except ValueError:
            return _ordinal_datetimems_to_datetime(ordinal_datetime)


def ordinal_time_to_calendar(ordinal_datetime: str, with_hours: bool = False) -> str:
    """
    Convert ordinal datetime format to calendar format.

    E.g., 2010-110(T10:12:14)" -> 2010-04-20(T10:12:14)

    Parameters
    ----------
    ordinal_datetime : str
        Datetime string of the form yyyy-jjj(THH:MM:SS)(.ffffff)
    with_hours : bool
        Return calendar with hours or not. Default is False.
    """
    has_hours = False
    # check if input has hours
    try:
        res = _ordinal_date_to_datetime(ordinal_datetime)
    except ValueError:
        has_hours = True
    time = ordinal_time_to_datetime(ordinal_datetime)
    if has_hours or with_hours is True:
        return time.isoformat()
    else:
        return time.strftime(calendar_date_format)


def calendar_to_ordinal_time(cal_datetime: str) -> str:
    """
    Convert calendar datetime format to ordinal datetime format.

    E.g., 2010-04-20(T10:12:14) -> 2010-110(T10:12:14)

    Parameters
    ----------
    cal_datetime : str
        Datestring of the form yyyy-mm-dd(THH:MM:SS)(.ffffff)
    """
    try:
        date = dt.datetime.strptime(cal_datetime, calendar_date_format)
    except ValueError:
        try:
            date = dt.datetime.strptime(cal_datetime, calendar_dt_format)
        except ValueError:
            date = dt.datetime.strptime(cal_datetime, calendar_dt_format_with_ms)
            return date.strftime(ordinal_dt_format_with_ms)
        else:
            return date.strftime(ordinal_dt_format)
    else:
        return date.strftime(ordinal_date_format)


def calendar_to_ordinal_datetime(cal_datetime: str) -> str:
    """
    Convert calendar datetime format to ordinal datetime format.

    E.g., 2010-04-20(T10:12:14) -> 2010-110(T10:12:14)

    Parameters
    ----------
    cal_datetime : str
        Datestring of the form yyyy-mm-dd(THH:MM:SS)(.ffffff)
    """
    try:
        cal_datetime.split(".")[1]
    except IndexError:
        source_format = calendar_dt_format
        target_format = ordinal_dt_format
    else:
        source_format = calendar_dt_format_with_ms
        target_format = ordinal_dt_format_with_ms
    date = dt.datetime.strptime(cal_datetime, source_format)
    return date.strftime(target_format)


def replace_all_ordinal_times(df: pd.DataFrame, timecol: str = "TIME"):
    """
    Convert all detected ordinal time columns in df to calendar format in place.

    All columns with timecol in the name will be converted and changes will be 
    implemented on incoming dataframe in place (no returned dataframe)!
    """
    for col in [col for col in df.columns if timecol in col]:
        if "T" in df[col].iloc[0]:
            df[col] = pd.to_datetime(df[col].map(ordinal_time_to_calendar))


## Network and file handling
def parse_http_date(http_date: str) -> dt.datetime:
    """Parse date string retrieved via urllib.request."""
    return dt.datetime(*eut.parsedate(http_date)[:6])


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
    return response.status_code < 400


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
