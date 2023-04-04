"""Scraper for Second Circuit
CourtID: ca2
Contact:
  Webmaster@ca2.uscourts.gov ('Calendar Team' handles updates, and is responsive)
  ecfhelpdesk@ca2.uscourts.gov
  Shane_Clouden@ca2.uscourts.gov
"""


import time
from datetime import date, timedelta

from dateutil.rrule import DAILY, rrule
from lxml import html

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interval = 30
        self.url = "http://www.ca2.uscourts.gov/decisions?IW_DATABASE=OPN&IW_FIELD_TEXT=*&IW_SORT=-Date"
        self.court_id = self.__module__
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                DAILY,
                interval=self.interval,
                dtstart=date(2007, 1, 1),
                until=date(2015, 1, 1),
            )
        ]

    def _get_case_names(self):
        return [titlecase(t) for t in self.html.xpath("//table/td[2]/text()")]

    def _get_download_urls(self):
        return [e for e in self.html.xpath("//table/td/b/a/@href")]

    def _get_case_dates(self):
        dates = []
        for e in self.html.xpath("//table/td[3]/text()"):
            dates.append(
                date.fromtimestamp(time.mktime(time.strptime(e, "%m-%d-%Y")))
            )
        return dates

    def _get_docket_numbers(self):
        return [
            e.text_content() for e in self.html.xpath("//table/td/b/a/nobr")
        ]

    def _get_precedential_statuses(self):
        statuses = []
        for status in self.html.xpath("//table/td[4]/text()"):
            if "opn" in status.lower():
                statuses.append("Published")
            elif "sum" in status.lower():
                statuses.append("Unpublished")
            else:
                statuses.append("Unknown")
        return statuses

    def _download_backwards(self, d):
        self.url = "http://www.ca2.uscourts.gov/decisions?IW_DATABASE=OPN&IW_FIELD_TEXT=*&IW_SORT=-Date&IW_BATCHSIZE=100&IW_FILTER_DATE_BEFORE={before}&IW_FILTER_DATE_After={after}".format(
            before=(d + timedelta(self.interval)).strftime("%Y%m%d"),
            after=d.strftime("%Y%m%d"),
        )
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
