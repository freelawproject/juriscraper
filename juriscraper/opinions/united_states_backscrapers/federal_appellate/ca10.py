import time
from datetime import date

from dateutil.rrule import DAILY, rrule
from lxml import html

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        self.url = "http://www.ca10.uscourts.gov/opinion/search/results?query=%20date%3A{}".format(
            today.strftime("%m/%d/%Y")
        )
        self.court_id = self.__module__
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                DAILY,
                dtstart=date(1995, 11, 1),
                until=date(2015, 1, 1),
            )
        ]
        self.base = (
            "//table[contains(concat('', @class, ''), 'search-results')]//tr"
        )

    def _get_case_names(self):
        return [
            e
            for e in self.html.xpath(
                f"{self.base}/td[@class='case-name']/text()"
            )
        ]

    def _get_download_urls(self):
        return [
            e
            for e in self.html.xpath(f"{self.base}/td[@class='link']/a/@href")
        ]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath(
            f"{self.base}/td[@class='publish-date']/text()"
        ):
            # ex: Nov-02-1995
            dates.append(
                date.fromtimestamp(
                    time.mktime(time.strptime(date_string, "%b-%d-%Y"))
                )
            )
        return dates

    def _get_docket_numbers(self):
        return [
            e
            for e in self.html.xpath(
                f"{self.base}/td[@class='case-no']/text()"
            )
        ]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_lower_courts(self):
        return [
            e
            for e in self.html.xpath(f"{self.base}/td[@class='origin']/text()")
        ]

    def _download_backwards(self, d):

        self.url = "http://www.ca10.uscourts.gov/opinion/search/results?query=%20date%3A{}".format(
            d.strftime("%m/%d/%Y")
        )

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
