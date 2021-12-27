# We import the entire datetime library because otherwise we run into
# conflicts in our isinstance statements.
import datetime
from datetime import date
from itertools import zip_longest
from math import ceil

from dateutil.parser import parser, parserinfo
from dateutil.rrule import DAILY, rrule

MISSPELLINGS = {
    "Febraury": "February",
    "Feburay": "February",
    "Sepetmber": "September",
    "Sepember": "September",
    "Term": "1",
}

json_date_handler = lambda obj: (
    obj.isoformat()
    if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date)
    else None
)


class BetterInfo(parserinfo):
    """Removes tokens to provide better support for splitting out multiple
    dates.

    By default, the JUMP variable is:

        JUMP = [" ", ".", ",", ";", "-", "/", "'",
                "at", "on", "and", "ad", "m", "t", "of",
                "st", "nd", "rd", "th"]

    This assumes that a single date is being sent to timesplit, and that that
    date might contain tokens like "and", ";", or "on". But when you're
    sending multiple dates, you are more likely to have something like this:

        'February 5, 1980; March 14, 1980 and May 28, 1980.

    This uses the semicolon and the word "and" to separate dates, so we need
    to allow them for splitting. This class makes that possible by removing
    them from the JUMP variable.
    """

    # m from a.m/p.m, t from ISO T separator
    JUMP = [
        " ",
        ".",
        ",",
        "-",
        "/",
        "'",
        "ad",
        "m",
        "t",
        "st",
        "nd",
        "rd",
        "th",
    ]

    def __init__(self):
        super().__init__()


p = parser(info=BetterInfo())
info = p.info


def timetoken(token):
    try:
        float(token)
        return True
    except ValueError:
        pass
    return any(
        f(token)
        for f in (
            info.jump,
            info.weekday,
            info.month,
            info.hms,
            info.ampm,
            info.pertain,
            info.utczone,
            info.tzoffset,
        )
    )


def quarter(month):
    """
    :int month: Any month, as an int.
    :return: The quarter of the year during which that month occurs (1-4)
    """
    return int(ceil(float(month) / 3))


def is_first_month_in_quarter(month):
    """

    :int month: Any month as an int.
    :return: Whether that month is the first month in a quarter
    """
    return month in [1, 4, 7, 10]


def fix_future_year_typo(future_date):
    """Fix current year typo, convert 2106 to 2016 in year 2016"""
    current_year = str(datetime.date.today().year)
    transposed_year = (
        current_year[0] + current_year[2] + current_year[1] + current_year[3]
    )
    if transposed_year == str(future_date.year):
        return datetime.date(
            int(current_year), future_date.month, future_date.day
        )
    return future_date


def make_date_range_tuples(start, end, gap):
    """Make an iterable of date tuples for use in iterating forms

    For example, a form might allow start and end dates and you want to iterate
    it one week at a time starting on Jan 1 and ending on Feb 3:

    >>> make_date_range_tuples(date(2017, 1, 1), date(2017, 2, 3), 7)
    [(Jan 1, Jan 7), (Jan 8, Jan 14), (Jan 15, Jan 21), (Jan 22, Jan 28),
     (Jan 29, Feb 3)]

    :param start: date when the query should start.
    :param end: date when the query should end.
    :param gap: the number of days, inclusive, that a query should span at a
    time.

    :rtype list(tuple)
    :returns: list of start, end tuples
    """
    # We create a list of start dates and a list of end dates, then zip them
    # together. If end_dates is shorter than start_dates, fill the last value
    # with the original end date.
    start_dates = [
        d.date() for d in rrule(DAILY, interval=gap, dtstart=start, until=end)
    ]
    end_start = start + datetime.timedelta(days=gap - 1)
    end_dates = [
        d.date()
        for d in rrule(DAILY, interval=gap, dtstart=end_start, until=end)
    ]
    return list(zip_longest(start_dates, end_dates, fillvalue=end))
