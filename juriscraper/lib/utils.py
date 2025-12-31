import re
import traceback
from datetime import date, datetime, timedelta
from itertools import chain, islice, tee
from typing import Any, Callable, Optional

from requests.exceptions import HTTPError

from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.log_tools import make_default_logger

from .date_utils import fix_future_year_typo
from .string_utils import (
    clean_string,
    convert_date_string,
    force_unicode,
    harmonize,
)

logger = make_default_logger()


def sanity_check_dates(dates_and_names: list[tuple], court_id: str) -> None:
    """Checks that dates are datetime.date objects and that they are not in the future

    :param dates_and_names: a 3 member tuple (case_date, case_name, date_is_approximate)
    :param court_id: for logging purposes
    """
    # check that no date is in the future
    future_date_count = 0
    for case_date, case_name, date_is_approximate in dates_and_names:
        if not isinstance(case_date, date):
            raise InsanityException(
                f"{court_id}: Member of case_dates list not a valid date object. "
                f"Instead it is: {type(case_date)} with value: {case_date}"
            )

        # If a date is approximate, then it may be set in the future until
        # half of the year has passed. Ignore this case
        # dates should not be in the future. Tolerate a week
        if not date_is_approximate and case_date > (
            date.today() + timedelta(days=7)
        ):
            future_date_count += 1
            error = f"{court_id}: {case_date} date is in the future. Case '{case_name}'"
            logger.error(error)

            # Interrupt data ingestion if more than 1 record has a bad date
            if future_date_count > 1:
                raise InsanityException(
                    f"More than 1 case has a date in the future. Last case: {error}"
                )


def sanity_check_case_names(case_names: list[str]) -> None:
    """Check that no name is an empty string

    :param case_names: ordered list of case names
    """
    prior_case_name = None
    for i, name in enumerate(case_names):
        if not name.strip():
            raise InsanityException(
                "Item with index %s has an empty case name. The prior "
                "item had case name of: %s" % (i, prior_case_name)
            )
        prior_case_name = name


def clean_attribute(name: str, value: Any) -> Any:
    """Performs standard cleaning by type; and some specific cleaning by name

    :param name: attribute standard name
    :param value: attribute value
    :return: cleaned value
    """
    if name == "download_urls":
        return value.strip()
    elif name == "case_dates" and not isinstance(value, (datetime, date)):
        value = convert_date_string(value)

    if isinstance(value, str):
        value = clean_string(value)
    elif isinstance(value, datetime):
        value = value.date()
        # Sanitize case date, fix typo of current year if present
        fixed_date = fix_future_year_typo(value)
        if fixed_date != value:
            logger.info("Date year typo detected. Converting %s to %s")
            value = fixed_date

    if name in ["case_names", "docket_numbers"]:
        value = harmonize(value)

    return value


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
        items = []
        for i in obj:
            items.append(clean_court_object(i))
        return items
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
