"""Scraper for the Michigan Court of Appeals
CourtID: michctapp
Court Short Name: Mich. Ct. App.
Type: Published
Reviewer: mlr
History:
 - 2014-09-19: Created by Jon Andersen
"""

import time
from datetime import date, timedelta

from juriscraper.opinions.united_states.state import mich


class Site(mich.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.today = date.today()
        self.a_while_ago = date.today() - timedelta(days=30)
        self.url = (
            "http://courts.mi.gov/opinions_orders/opinions_orders"
            "/Pages/default.aspx?SearchType=4"
            "&Status_Advanced=coapub&FirstDate_Advanced="
            "{start_month}%2f{start_day}%2f{start_year}"
            "&LastDate_Advanced="
            "{end_month}%2f{end_day}%2f{end_year}".format(
                start_day=self.a_while_ago.day,
                start_month=self.a_while_ago.month,
                start_year=self.a_while_ago.year,
                end_day=self.today.day,
                end_month=self.today.month,
                end_year=self.today.year,
            )
        )
        self.back_scrape_iterable = list(range(0, 200))
        self.court_id = self.__module__

    def _download_backwards(self, page):
        self.url = (
            "http://courts.mi.gov/opinions_orders/opinions_orders/Pages/default.aspx?SearchType=4&Status_Advanced=coapub&FirstDate_Advanced=1%2f1%2f1900&LastDate_Advanced=9%2f19%2f2014&PageIndex="
            + str(page)
        )
        time.sleep(6)  # This site throttles if faster than 2 hits / 5s.
        self.html = self._download()
