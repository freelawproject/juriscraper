# Scraper for Florida Supreme Court
# CourtID: fla
# Court Short Name: fla

from datetime import date, datetime, timedelta
from typing import Dict, Optional, Tuple

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import make_date_range_tuples
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # make a backscrape request every `days_interval` range, to avoid pagination
    days_interval = 20
    first_opinion_date = datetime(1999, 9, 23)
    # even though you can put whatevere number you want as limit, 50 seems to be max
    base_url = "https://www.floridasupremecourt.org/search/?searchtype=opinions&limit=50&startdate={}&enddate={}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.set_url()
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parses HTML into case dictionaries

        :return: None
        """
        path = '//div[@class="search-results"]//tbody/tr'
        for row in self.html.xpath(path):
            cells = row.xpath("td")
            url = cells[4].xpath("a/@href")
            name = cells[2].text_content().strip()

            if not url or not name:
                # Skip rows without PDFs or without case names
                continue

            self.cases.append(
                {
                    "url": url[0],
                    "docket": cells[1].text_content().strip(),
                    "name": name,
                    "date": cells[0].text_content().strip(),
                    "status": self.status,
                }
            )

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Sets URL using date arguments

        If not dates are passed, get 50 most recent opinions

        :param start: start date
        :param end: end date
        :return: none
        """
        if not start:
            end = datetime.today()
            start = end - timedelta(days=365)

        fmt = "%m/%d/%Y"
        self.url = self.base_url.format(start.strftime(fmt), end.strftime(fmt))

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Overrides scraper URL using date inputs

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.set_url(*dates)
        logger.info("Backscraping for range %s %s", *dates)

    def make_backscrape_iterable(self, kwargs: Dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        :param kwargs: passed when initializing the scraper, may or
        may not contain backscrape controlling arguments

        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%m/%d/%Y")
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = datetime.now()

        self.back_scrape_iterable = make_date_range_tuples(
            start, end, self.days_interval
        )
