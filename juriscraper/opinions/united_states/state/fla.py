# Scraper for Florida Supreme Court
# CourtID: fla
# Court Short Name: fla

from datetime import date, datetime, timedelta
from typing import Dict, Tuple

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import make_date_range_tuples
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"

        today = datetime.today()
        today_last_year = today - timedelta(days=365)
        fmt = self.url_date_format = "%m/%d/%Y"

        # Get 50 most recent opinions from past year--even though you can
        # put whatever number you want as limit, 50 seems to be max
        self.base_url = "https://www.floridasupremecourt.org/search/?searchtype=opinions&limit=50&startdate={}&enddate={}"
        self.url = self.base_url.format(
            today_last_year.strftime(fmt), today.strftime(fmt)
        )

        # make a backscrape request every `days_interval` range, to avoid pagination
        self.days_interval = 60
        self.first_opinion_date = datetime(1999, 9, 23)
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parses HTML into case dictionaries

        :return: None
        """
        path = '//div[@class="search-results"]//tbody/tr'
        for row in self.html.xpath(path):
            cells = row.xpath("td")
            url = cells[4].xpath("a/@href")

            if not url:
                # Skip rows without PDFs
                continue

            self.cases.append(
                {
                    "url": url[0],
                    "docket": cells[1].text_content().strip(),
                    "name": cells[2].text_content().strip(),
                    "date": cells[0].text_content().strip(),
                    "status": self.status,
                }
            )

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Overrides scraper URL using date inputs

        :param dates: (start_date, end_date) tuple
        :return None
        """
        start, end = dates
        self.url = self.base_url.format(
            start.strftime(self.url_date_format),
            end.strftime(self.url_date_format),
        )
        logger.info("Backscraping for range %s %s", start, end)

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
