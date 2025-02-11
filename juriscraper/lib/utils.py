import re
import traceback
from datetime import date, datetime
from itertools import chain, islice, tee
from typing import Callable, Optional

from requests.exceptions import HTTPError

from juriscraper.AbstractSite import logger

from .string_utils import force_unicode


def previous_and_next(some_iterable):
    """Provide previous and next values while iterating a list.

    This is from: http://stackoverflow.com/a/1012089/64911

    This will allow you to lazily iterate a list such that as you iterate, you
    get a tuple containing the previous, current, and next value.
    """
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)


def clean_court_object(obj):
    """Clean a list or dict that is part of a scraping response.

    Court data is notoriously horrible, so this function attempts to clean up
    common problems that it may have. You can pass in either a dict or a list,
    and it will be cleaned recursively.

    Supported cleanup includes:

    1. Removing spaces before commas.
    1. Stripping whitespace from the ends.
    1. Normalizing white space.
    1. Forcing unicode.

    :param obj: A dict or list containing string objects.
    :return: A dict or list with the string values cleaned.
    """
    if isinstance(obj, list):
        l = []
        for i in obj:
            l.append(clean_court_object(i))
        return l
    elif isinstance(obj, dict):
        d = {}
        for k, v in obj.items():
            d[k] = clean_court_object(v)
        return d
    elif isinstance(obj, str):
        s = " ".join(obj.strip().split())
        s = force_unicode(s)
        return re.sub(r"\s+,", ",", s)
    else:
        return obj


def backscrape_over_paginated_results(
    first_page: int,
    last_page: int,
    start_date: date,
    end_date: date,
    date_fmt: str,
    site,
    prepare_request_fn: Optional[Callable] = None,
    url_template: str = "",
) -> list[dict]:
    """
    Iterates over consecutive pages, looking for cases in a specific date range
    Of use when the page offers no date filters, so one must look through all
    the pages. Assumes the page is returning results ordered by date

    :param first_page: integer of the first page
    :param last_page: integer of the last page
    :param start_date: cases with a date greater than this value will be collected
    :param end_date: cases with a date lesses than this value will be collected
    :param date_fmt: date format to parse case dates
    :param site: the site object
    :prepare_request_fn: a function that takes as arguments the page number
        and the site object, and modifies the site's attribute to prepare
        the request before `site._download()` is called.
        If not passed, it will try to use the url_template argument
    :param url_template: string to apply .format() to, like "url&page={}"
        where the argument to pass will be the page number

    :return: the list of cases between the dates
    """
    cases = []

    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()

    for page in range(first_page, last_page):
        site.cases = []  # reset results container

        if prepare_request_fn:
            prepare_request_fn(page, site)
        else:
            site.url = url_template.format(page)

        try:
            site.html = site._download()
            site._process_html()
        except HTTPError:
            # if the request returned and error, take advantage of the cases
            # already downloaded. This may also be a case when the last page
            # was unknown, and `last_page + 1` generates an error
            logger.info(
                "Error while downloading, breaking pagination at page %s", page
            )
            logger.debug("%s", traceback.format_exc())
            break

        if not site.cases:
            logger.info("No cases in this page; breaking the loop")
            break

        # results are ordered by desceding date
        earliest = datetime.strptime(site.cases[-1]["date"], date_fmt).date()
        latest = datetime.strptime(site.cases[0]["date"], date_fmt).date()
        logger.info(
            "Results page %s has date range %s to %s", page, earliest, latest
        )

        # no intersection between date ranges
        if max(earliest, start_date) >= min(latest, end_date):
            # if earliest date from results is earlier than
            # the start date, no need to iterate any further
            if earliest < start_date:
                logger.info(
                    "Finishing backscrape: earliest results date is %s earlier than start %s",
                    earliest,
                    start_date,
                )
                break
            continue

        # if there is an intersection, test every case and
        # collect the matching cases
        for case in site.cases:
            case_date = datetime.strptime(case["date"], date_fmt).date()
            if case_date < end_date and case_date > start_date:
                cases.append(case)

    return cases
