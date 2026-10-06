import importlib
import inspect
import logging
import pkgutil
import unittest
from datetime import date, datetime
from itertools import product

from juriscraper import opinions, oral_args
from juriscraper.AbstractSite import AbstractSite
from juriscraper.Backscraper import (
    Backscraper,
    DateBackscraper,
    PageIndexBackscraper,
    YearBackscraper,
)

# Formats seen across scrapers, to write a valid date in a format that
# doesn't match the scraper's `date_format`. Jan 31 can't be read with the
# day and month swapped, so these never parse by accident
DATE_FORMATS = ("%Y/%m/%d", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d")
SAMPLE_DATE = date(2024, 1, 31)

# Non-empty strings that aren't a date in any format
NOT_A_DATE = ("not a date", "2024", "2024/13/45", "2024-01-31T00:00:00")

# Non-empty strings that aren't a "YYYY" year
WRONG_YEARS = ("2024/01/31", "24", "20245", " 2024", "2024.0", "year")

# Non-empty strings that aren't a page index
WRONG_PAGES = ("page 2", "-1", "1.5", "first")

# Non-empty values that aren't strings, e.g. already parsed by a caller
NOT_STRINGS = (date(2024, 1, 31), datetime(2024, 1, 31), 2024)


def find_backscrapers(
    base: type[Backscraper],
) -> list[tuple[str, type[Backscraper]]]:
    """Return (module name, class) for every class inheriting `base`, in
    the opinion and oral argument scraper packages

    Walks every module instead of using `build_module_list`, which follows
    the `__all__` lists: a scraper missing from `__all__` (e.g.
    `federal_district.ed_louisiana`) must be tested too.

    :param base: a `Backscraper` family, e.g. `DateBackscraper`
    :return: the matching classes, sorted by module
    """
    backscrapers = []
    for package in (opinions, oral_args):
        prefix = f"{package.__name__}."
        for module_info in pkgutil.walk_packages(package.__path__, prefix):
            module = importlib.import_module(module_info.name)
            for _, cls in inspect.getmembers(module, inspect.isclass):
                # Only classes defined in this module, not imported ones
                if cls.__module__ == module.__name__ and issubclass(cls, base):
                    backscrapers.append((module.__name__, cls))
    return sorted(backscrapers, key=lambda pair: pair[0])


def backscrape_kwargs(start=None, end=None) -> dict:
    """Backscrape kwargs as CourtListener sends them."""
    return {
        "backscrape_start": start,
        "backscrape_end": end,
        "days_interval": None,
    }


async def run_download_backwards(
    site_class: type[AbstractSite, Backscraper], item: object
) -> tuple[bool, str | None]:
    """Run `_download_backwards(item)` offline, like #1900's tier 2a

    As `importer.site_yielder` does, the item goes to a fresh Site built
    without kwargs. `_download` is replaced by a stub that records the call,
    and `_process_html` by a no-op, so only the scraper-specific logic runs:
    unpacking the item, formatting it, building the URL or payload.

    :param site_class: a Site class inheriting `Backscraper`
    :param item: an item of its `back_scrape_iterable`
    :return: whether `_download` was called, and the Site's url
    """
    site = site_class()
    downloaded = False

    async def fake_download(*args, **kwargs):
        nonlocal downloaded
        downloaded = True
        site.downloader_executed = True

    site._download = fake_download
    # Match the scraper's signature: some `_process_html` are async
    if inspect.iscoroutinefunction(site._process_html):

        async def no_op():
            pass
    else:

        def no_op():
            pass

    site._process_html = no_op
    try:
        await site._download_backwards(item)
    finally:
        await site.close_session()
    return downloaded, site.url


class DateBackscraperTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.addCleanup(logging.disable, logging.NOTSET)
        self.backscrapers: list[
            tuple[str, type[AbstractSite, DateBackscraper]]
        ] = find_backscrapers(DateBackscraper)

        self.assertTrue(self.backscrapers, "No DateBackscraper found")

    @staticmethod
    def wrong_kwargs(date_format: str) -> list[tuple[dict, type[Exception]]]:
        """Backscrape kwargs that must be rejected, and the expected error

        :param date_format: the scraper's `date_format`
        :return: (kwargs, exception) pairs
        """
        wrong_dates = [
            SAMPLE_DATE.strftime(f) for f in DATE_FORMATS if f != date_format
        ] + list(NOT_A_DATE)
        later = date(2022, 6, 20).strftime(date_format)
        earlier = date(2020, 1, 15).strftime(date_format)
        return (
            [(backscrape_kwargs(start=v), ValueError) for v in wrong_dates]
            + [(backscrape_kwargs(end=v), ValueError) for v in wrong_dates]
            + [(backscrape_kwargs(start=v), TypeError) for v in NOT_STRINGS]
            + [(backscrape_kwargs(end=v), TypeError) for v in NOT_STRINGS]
            + [(backscrape_kwargs(start=later, end=earlier), ValueError)]
        )

    def test_wrong_kwargs_raise(self) -> None:
        """A wrong format raises ValueError, a non-string TypeError, and a
        start after the end ValueError"""
        cases = [
            (module, site_class, kwargs, error)
            for module, site_class in self.backscrapers
            for kwargs, error in self.wrong_kwargs(site_class.date_format)
        ]
        for module, site_class, kwargs, error in cases:
            with (
                self.subTest(module=module, kwargs=kwargs),
                self.assertRaises(error),
            ):
                site_class(**kwargs)

    async def test_download_backwards_accepts_items(self) -> None:
        """Without kwargs and with a valid range, `back_scrape_iterable`
        isn't empty, and `_download_backwards` accepts its first and last
        items"""
        cases = [
            (module, site_class, kwargs)
            for module, site_class in self.backscrapers
            for kwargs in (
                {},
                backscrape_kwargs(
                    start=date(2020, 1, 15).strftime(site_class.date_format),
                    end=date(2022, 6, 20).strftime(site_class.date_format),
                ),
            )
        ]
        for module, site_class, kwargs in cases:
            with self.subTest(module=module, kwargs=kwargs):
                self.assertIsNot(
                    site_class._download_backwards,
                    AbstractSite._download_backwards,
                    "doesn't override _download_backwards",
                )
                items = list(site_class(**kwargs).back_scrape_iterable)
                self.assertTrue(items, "back_scrape_iterable is empty")

                downloaded, url = await run_download_backwards(
                    site_class, items[0]
                )
                self.assertTrue(downloaded or url, f"first item {items[0]}")
                downloaded, url = await run_download_backwards(
                    site_class, items[-1]
                )
                self.assertTrue(downloaded or url, f"last item {items[-1]}")


class YearBackscraperTest(unittest.IsolatedAsyncioTestCase):
    WRONG_KWARGS = (
        [(backscrape_kwargs(start=v), ValueError) for v in WRONG_YEARS]
        + [(backscrape_kwargs(end=v), ValueError) for v in WRONG_YEARS]
        + [(backscrape_kwargs(start=v), TypeError) for v in NOT_STRINGS]
        + [(backscrape_kwargs(end=v), TypeError) for v in NOT_STRINGS]
        + [(backscrape_kwargs(start="2022", end="2020"), ValueError)]
    )
    VALID_KWARGS = ({}, backscrape_kwargs(start="2020", end="2022"))

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.addCleanup(logging.disable, logging.NOTSET)
        self.backscrapers: list[
            tuple[str, type[AbstractSite, YearBackscraper]]
        ] = find_backscrapers(YearBackscraper)

        self.assertTrue(self.backscrapers, "No YearBackscraper found")

    def test_wrong_kwargs_raise(self) -> None:
        """A wrong "YYYY" year raises ValueError, a non-string TypeError, and
        a start after the end ValueError"""
        cases = product(self.backscrapers, self.WRONG_KWARGS)
        for (module, site_class), (kwargs, error) in cases:
            with (
                self.subTest(module=module, kwargs=kwargs),
                self.assertRaises(error),
            ):
                site_class(**kwargs)

    async def test_download_backwards_accepts_items(self) -> None:
        """Without kwargs and with a valid range, `back_scrape_iterable`
        isn't empty, and `_download_backwards` accepts its first and last
        items"""
        cases = product(self.backscrapers, self.VALID_KWARGS)
        for (module, site_class), kwargs in cases:
            with self.subTest(module=module, kwargs=kwargs):
                self.assertIsNot(
                    site_class._download_backwards,
                    AbstractSite._download_backwards,
                    "doesn't override _download_backwards",
                )
                items = list(site_class(**kwargs).back_scrape_iterable)
                self.assertTrue(items, "back_scrape_iterable is empty")

                downloaded, url = await run_download_backwards(
                    site_class, items[0]
                )
                self.assertTrue(downloaded or url, f"first item {items[0]}")
                downloaded, url = await run_download_backwards(
                    site_class, items[-1]
                )
                self.assertTrue(downloaded or url, f"last item {items[-1]}")


class PageIndexBackscraperTest(YearBackscraperTest):
    """Same tests as YearBackscraperTest, with page indexes"""

    WRONG_KWARGS = (
        [(backscrape_kwargs(start=v), ValueError) for v in WRONG_PAGES]
        + [(backscrape_kwargs(end=v), ValueError) for v in WRONG_PAGES]
        + [(backscrape_kwargs(start=v), TypeError) for v in NOT_STRINGS]
        + [(backscrape_kwargs(end=v), TypeError) for v in NOT_STRINGS]
        + [(backscrape_kwargs(start="5", end="2"), ValueError)]
    )
    VALID_KWARGS = ({}, backscrape_kwargs(start="2", end="5"))

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.addCleanup(logging.disable, logging.NOTSET)
        self.backscrapers = find_backscrapers(PageIndexBackscraper)
        self.assertTrue(self.backscrapers, "No PageIndexBackscraper found")
