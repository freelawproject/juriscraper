from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Generic, TypeVar

from juriscraper.lib.date_utils import make_date_range_tuples

IterableItemT = TypeVar("IterableItemT")


class Backscraper(ABC, Generic[IterableItemT]):
    """Mixin for Sites that download their historical records

    The Site builds `back_scrape_iterable` in `__init__`, and
    `_download_backwards` receives one of its items at a time.

    List the family before the Site's base class, e.g.
    `class Site(DateBackscraper, OpinionSiteLinear)`,
    so its methods take precedence over `AbstractSite`'s
    backscrape defaults.

    Add it to the class that defines `_download_backwards`: on a subclass,
    the family's abstract method would shadow the parent Site's implementation.
    """

    # Any iterable: scrapers assign and post-process it in many ways
    back_scrape_iterable: Any = None

    @abstractmethod
    async def _download_backwards(
        self, iterable_item: IterableItemT, /
    ) -> None:
        """Download and process the records for one iterable item

        :param iterable_item: an item of `self.back_scrape_iterable`
        """
        raise NotImplementedError


class DateBackscraper(Backscraper[IterableItemT], ABC):
    """Backscraper whose `backscrape_start` and `backscrape_end` are dates

    Builds (start, end) windows of `days_interval` days, from
    `first_opinion_date` until today by default. Sites needing other items
    override `make_backscrape_iterable` and reuse
    `get_backscrape_date_range`, e.g. `bap9` (one window), `dcd` (years).
    Set `date_format` when the Site's callers use another format.
    """

    first_opinion_date: date
    days_interval: int
    # A few scrapers override it; move them to the default and remove it
    date_format: str = "%Y/%m/%d"

    def parse_backscrape_date(self, value: object, name: str) -> date | None:
        """Parse a `date_format` string; None if the value isn't given

        :param value: the kwarg value
        :param name: the kwarg name, for error messages
        """
        if not value:
            return None
        if not isinstance(value, str):
            raise TypeError(
                f"{name}={value!r} must be a string in "
                f"{self.date_format!r} format"
            )
        try:
            return datetime.strptime(value, self.date_format).date()
        except ValueError as e:
            raise ValueError(
                f"{name}={value!r} must be a date in "
                f"{self.date_format!r} format"
            ) from e

    def get_backscrape_date_range(self, kwargs: dict) -> tuple[date, date]:
        """Parse the (start, end) range, both ends inclusive; defaults to
        `first_opinion_date` and today

        :param kwargs: the kwargs passed to `Site.__init__`
        """
        start = self.parse_backscrape_date(
            kwargs.get("backscrape_start"), "backscrape_start"
        )
        end = self.parse_backscrape_date(
            kwargs.get("backscrape_end"), "backscrape_end"
        )

        if start is None:
            if not hasattr(self, "first_opinion_date"):
                # A scraper misconfiguration, not a bad kwarg
                raise AttributeError(
                    f"{type(self).__name__} has no `first_opinion_date` "
                    "default for a missing `backscrape_start`"
                )
            start = self.first_opinion_date
        if end is None:
            end = date.today()

        # `first_opinion_date` may be a datetime, which can't be compared
        # with a date
        start_day = start.date() if isinstance(start, datetime) else start
        if start_day > end:
            raise ValueError(
                f"backscrape_start {start_day} is after backscrape_end {end}"
            )
        return start, end

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Set `back_scrape_iterable` to (start, end) windows of
        `days_interval` days (the kwarg, or the class attribute)

        :param kwargs: the kwargs passed to `Site.__init__`
        """
        start, end = self.get_backscrape_date_range(kwargs)
        days_interval = kwargs.get("days_interval")

        if not days_interval:
            if hasattr(self, "days_interval"):
                days_interval = self.days_interval
            else:
                # A scraper misconfiguration, not a bad kwarg
                raise AttributeError(
                    f"{type(self).__name__} has no `days_interval` default "
                    "for a missing `days_interval` kwarg"
                )

        self.back_scrape_iterable = make_date_range_tuples(
            start, end, days_interval
        )


class YearBackscraper(Backscraper[IterableItemT], ABC):
    """Backscraper whose `backscrape_start` and `backscrape_end` are "YYYY"
    years

    Builds one `int` per year, both ends inclusive, from the year of
    `first_opinion_date` until the current year by default.
    """

    first_opinion_date: date

    @staticmethod
    def parse_backscrape_year(value: object, name: str) -> int | None:
        """Parse a "YYYY" string; None if the value isn't given

        :param value: the kwarg value
        :param name: the kwarg name, for error messages
        """
        if not value:
            return None
        if not isinstance(value, str):
            raise TypeError(f"{name}={value!r} must be a 'YYYY' string")
        if not (len(value) == 4 and value.isdigit()):
            raise ValueError(
                f"{name}={value!r} must be a year in 'YYYY' format"
            )
        return int(value)

    def get_backscrape_year_range(self, kwargs: dict) -> tuple[int, int]:
        """Parse the (start, end) years, both inclusive; defaults to the
        year of `first_opinion_date` and the current year

        :param kwargs: the kwargs passed to `Site.__init__`
        """
        start_year = self.parse_backscrape_year(
            kwargs.get("backscrape_start"), "backscrape_start"
        )
        end_year = self.parse_backscrape_year(
            kwargs.get("backscrape_end"), "backscrape_end"
        )

        if start_year is None:
            if not hasattr(self, "first_opinion_date"):
                # A scraper misconfiguration, not a bad kwarg
                raise AttributeError(
                    f"{type(self).__name__} has no `first_opinion_date` "
                    "default for a missing `backscrape_start`"
                )
            start_year = self.first_opinion_date.year
        if end_year is None:
            end_year = date.today().year

        if start_year > end_year:
            raise ValueError(
                f"backscrape_start {start_year} is after backscrape_end {end_year}"
            )
        return start_year, end_year

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Set `back_scrape_iterable` to every year of the range

        :param kwargs: the kwargs passed to `Site.__init__`
        """
        start, end = self.get_backscrape_year_range(kwargs)
        self.back_scrape_iterable = list(range(start, end + 1))


class PageIndexBackscraper(Backscraper[IterableItemT], ABC):
    """Backscraper whose `backscrape_start` and `backscrape_end` are page
    indexes, for sources that only paginate their archive (no dates or
    years to filter by)

    Builds one `int` per page, both ends inclusive, from `first_page_index`
    to `last_page_index` by default. Set `reverse_page_order` to walk from
    the last page to the first, e.g. to scrape the oldest pages first.
    """

    first_page_index: int
    last_page_index: int
    reverse_page_order: bool = False

    @staticmethod
    def parse_backscrape_page_index(value: object, name: str) -> int | None:
        """Parse a page index string; None if the value isn't given

        :param value: the kwarg value
        :param name: the kwarg name, for error messages
        """
        if not value:
            return None
        if not isinstance(value, str):
            raise TypeError(f"{name}={value!r} must be a page index string")
        if not value.isdigit():
            raise ValueError(f"{name}={value!r} must be a page index")
        return int(value)

    def get_backscrape_page_range(self, kwargs: dict) -> tuple[int, int]:
        """Parse the (start, end) page indexes, both inclusive; defaults to
        `first_page_index` and `last_page_index`

        :param kwargs: the kwargs passed to `Site.__init__`
        """
        start = self.parse_backscrape_page_index(
            kwargs.get("backscrape_start"), "backscrape_start"
        )
        end = self.parse_backscrape_page_index(
            kwargs.get("backscrape_end"), "backscrape_end"
        )

        if start is None:
            start = self._page_index_default("first_page_index")
        if end is None:
            end = self._page_index_default("last_page_index")

        if start > end:
            raise ValueError(
                f"backscrape_start {start} is after backscrape_end {end}"
            )
        return start, end

    def _page_index_default(self, attribute: str) -> int:
        """The class attribute used when a page index kwarg isn't given"""
        if not hasattr(self, attribute):
            # A scraper misconfiguration, not a bad kwarg
            raise AttributeError(
                f"{type(self).__name__} has no `{attribute}` default"
            )
        return getattr(self, attribute)

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Set `back_scrape_iterable` to every page index of the range, in
        `reverse_page_order` if set

        :param kwargs: the kwargs passed to `Site.__init__`
        """
        start, end = self.get_backscrape_page_range(kwargs)
        pages = list(range(start, end + 1))
        self.back_scrape_iterable = (
            pages[::-1] if self.reverse_page_order else pages
        )
