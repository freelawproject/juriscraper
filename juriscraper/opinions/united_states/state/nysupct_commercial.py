"""Scraper and Back Scraper for New York Commercial Division
CourtID: nysupct_commercial
Court Short Name: NY
History:
 - 2024-01-05, grossir: modified to use nytrial template
"""

from datetime import date, datetime

from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    base_url = "https://nycourts.gov/reporter/slipidx/com_div_idxtable.shtml"
    court_regex = r".*"
    first_opinion_date = date(2013, 7, 1)

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for i in range(start_date.month, end_date.month+1):
            if i==end_date.month:
                self.url=self.build_url()
            else:
                self.url=self.build_url(datetime(year=start_date.year,month=i,day=start_date.day))
            self.parse()
            self.downloader_executed=False
        return 0

    def get_class_name(self):
        return "nysupct_commercial"

    def get_court_name(self):
        return "New York Supreme Court Commercial Division"
