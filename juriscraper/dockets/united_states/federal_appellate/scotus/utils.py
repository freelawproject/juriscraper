"""Utilities for SCOTUS docket scraping and processing."""

from datetime import date, datetime, timedelta
from hashlib import sha1
import re

import dateutil.parser


"""Text utilities

Note: PDF parsing can return various Unicode dashes beyond the standard 
hyphen-minus character (U+002d). The docket search pattern uses U+002d, 
U+2010, U+2011, U+2012, U+2013, and U+2014.
"""

# parse docket numbers
dash_pat = r"[\u002d\u2010\u2011\u2012\u2013\u2014]"
dash_regex = re.compile(dash_pat)
docket_pat = r"\d{2}[\u002d\u2010\u2011\u2012\u2013\u2014AaMmOo]\d{1,5}"
docket_number_regex = re.compile(docket_pat)
docket_num_strict_regex = re.compile(r"(\d\d)([-AOM])(\d{1,5})")

# parse docket PDF filing URLs
filing_url_regex = re.compile(
    (
        r"(?<=www\.supremecourt\.gov)(?:/\w+?/)"
        r"(?P<term>\d\d)/"
        r"(?P<docketnum>\d{2}[-AMO]\d{1,5})/"
        r"(?P<entrynum>\d+)/"
        r"(?P<timestamp>\d{17})"
    )
)


# special treatment for Orders PDFs
_orders_pat = (
    r"(?<=No\. )\d{2}[\u002d\u2010\u2011\u2012\u2013\u2014AaMmOo]\d{1,5}(?=\.)"
    r"|(?<=\n)\d{2}[\u002d\u2010\u2011\u2012\u2013\u2014AaMmOo]\d{1,5}"
    r"|(?<=\()\d{2}[\u002d\u2010\u2011\u2012\u2013\u2014AaMmOo]\d{1,5}(?=\))"
)
orders_docket_regex = re.compile(_orders_pat)

"""multiple dispatch docket number formatters"""


def dedocket(docket_number: str) -> tuple:
    """Accept a padded docket string and return components of a docket number
    as a tuple e.g. (2023, '-', 5) or (2017, 'A', 54)."""
    term, mod, casenum = [docket_number[i:j] for i, j in ((0, 2), (2, 3), (3, 8))]
    return int("20" + term), mod.upper(), int(casenum)


def padocket(x) -> str:
    """Accept unpadded docket number string or a tuple of docket number components
    and return padded docket string formatted as e.g. '23-00005' or '17A00054'.
    """
    if isinstance(x, (list, tuple)):
        assert len(x) == 3
        yyyy, docket_type, case_num = x
        assert (
            isinstance(yyyy, int)
            and yyyy >= 2007
            and docket_type.upper() in {"-", "A", "M", "O"}
            and isinstance(case_num, int)
        )
        return str(yyyy)[2:4] + docket_type + ("0000" + str(case_num))[-5:]
    elif isinstance(x, str):
        assert docket_number_regex.search(x), f"{x} not a docket number"
        return x[:3] + ("0000" + str(int(x[3:])))[-5:]


def endocket(x) -> str:
    """Accept padded docket number string or a tuple of docket number components
    and return unpadded docket string formatted as e.g. '23-5' or '17A54'."""
    if isinstance(x, (list, tuple)):
        assert len(x) == 3
        yyyy, docket_type, case_num = x
        assert (
            isinstance(yyyy, int)
            and yyyy >= 2007
            and docket_type.upper() in {"-", "A", "M", "O"}
            and isinstance(case_num, int)
        )
        return str(yyyy)[2:4] + docket_type + str(case_num)
    elif isinstance(x, str):
        assert docket_number_regex.search(x)
        return x[:3] + str(int(x[3:]))


def docket_priority(x: list) -> list:
    """Sort key for docket numbers in order of 1) type ('-', 'A', 'M'), 2) year DESC,
    3) case number ASC. This prioritizes most recent dockets, then appeals, then motions.
    """
    type_priority = {"-": 0, "A": 1, "M": 2, "O": 3}
    term, mod, casenum = dedocket(x)
    return (type_priority[mod], 1 / term, casenum)


"""Date utilities"""


def makedate(d, **kwargs) -> date:
    """Allow `datetime` objects to bypass `dateparser.parse`; a TypeError would
    otherwise be raised."""
    if isinstance(d, (datetime, date)) or d is None:
        return d
    else:
        # return dateparser.parse(d)
        return dateutil.parser.parse(d, **kwargs)


def next_weekday(d: date) -> date:
    """Bump the input date object to the next weekday if it falls on a weekend."""
    if (reldate := d.weekday() - 7) < -2:
        # it's a weekday; no-op
        return d
    else:
        return d + timedelta(hours=(-24 * reldate))


def first_monday_oct(year: int) -> date:
    """Find the first Monday in October of `year`."""
    for i in range(1, 8):
        if (term_start := date(year, 10, i)).weekday() == 0:
            return term_start


def which_term(d: date) -> int:
    """Returns the SCOTUS term year for the passed date."""
    _date = makedate(d)
    if _date >= first_monday_oct(_date.year):
        return _date.year
    else:
        return _date.year - 1


def current_term() -> date:
    """Returns the current SCOTUS term year, running Oct-Sep."""
    return which_term(date.today())


def current_term_start():
    """Returns the current SCOTUS term start date."""
    return first_monday_oct(current_term().year)


def parse_filing_timestamp(ts):
    """Instantiate a datetime.datetime object with the parsed result of
    the 17-digit timestamp embedded in PDF filing URLs.

    From:

    <http://www.supremecourt.gov/DocketPDF/21/21-1/181253
    /20210609120636723_merged%20final%20cert%20petition.pdf>

    take '20210609120636723'.
    """
    argz = (
        ts[:4],
        ts[4:6],
        ts[6:8],
        ts[8:10],
        ts[10:12],
        ts[12:14],
        ts[14:] + "000",
    )
    return datetime(*[int(x) for x in argz])


"""Miscellaneous utilities"""


def make_hash(b: bytes) -> str:
    """Make a unique ID. ETag and Last-Modified from courts cannot be
    trusted.
    """
    return sha1(b, usedforsecurity=False).hexdigest()


def chunker(iterable, chunksize=100):
    """Break a large iterable into a generator of smaller chunks.

    Note
    ====
    Iterating over `iterable` in a listcomp will return None when `chunksize`
    is greater than `len(iterable)` because the `iterable` is always exhausted
    before the listcomp can be completed. Use this instead."""

    # wrap `iterable` if it doesn't quack like an iterable
    if not hasattr(iterable, "__next__"):
        iterable = iter(iterable)

    while True:
        chunk = []
        for i in range(chunksize):
            try:
                chunk.append(next(iterable))
            except StopIteration:
                # yield what has been iterated so far
                break
        if chunk == []:
            return  # not StopIteration; see PEP 479 para 10
        else:
            yield chunk
