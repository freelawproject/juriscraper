from datetime import date, datetime

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.html_utils import (
    get_row_column_links,
    get_row_column_text,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    first_opinion_date = datetime(2019, 7, 17)
    days_interval = 28  # Monthly interval

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.la2nd.org/opinions/"
        self.year = datetime.now().year
        self.url = f"{self.base_url}?opinion_year={self.year}"
        self.cases = []
        self.status = "Published"
        self.target_date = None
        self.make_backscrape_iterable(kwargs)

    def _download(self):
        html = super()._download()
        if html is not None:
            tables = html.cssselect("table#datatable")
            if not tables or not tables[0].cssselect("tbody tr"):
                self.year -= 1
                self.url = f"{self.base_url}?opinion_year={self.year}"
                return self._download()
        return html

    def _process_html(self):
        if self.html is None:
            return

        tables = self.html.cssselect("table#datatable")
        if tables and tables[0].cssselect("tbody tr"):
            logger.info(f"Processing cases for year: {self.year}")
            for row in tables[0].cssselect("tbody tr"):
                case_date = datetime.strptime(
                    get_row_column_text(row, 1), "%m/%d/%Y"
                ).date()

                # Skip if before first opinion date
                if case_date < self.first_opinion_date.date():
                    continue

                # Only apply date filtering during backscrape
                if (
                    hasattr(self, "back_scrape_iterable")
                    and self.back_scrape_iterable
                ):
                    if self.target_date:
                        target_month = self.target_date.month
                        target_year = self.target_date.year
                        if (
                            case_date.year != target_year
                            or case_date.month != target_month
                        ):
                            continue

                self.cases.append(
                    {
                        "date": get_row_column_text(row, 1),
                        "docket": get_row_column_text(row, 2),
                        "name": get_row_column_text(row, 3),
                        "author": get_row_column_text(row, 4),
                        "disposition": get_row_column_text(row, 5),
                        "lower_court": get_row_column_text(row, 6),
                        "summary": get_row_column_text(row, 7),
                        "url": get_row_column_links(row, 8),
                    }
                )

    def _download_backwards(self, target_date: date) -> None:
        logger.info(f"Backscraping for date: {target_date}")
        self.target_date = target_date
        self.year = target_date.year
        self.url = f"{self.base_url}?opinion_year={self.year}"
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs):
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )
