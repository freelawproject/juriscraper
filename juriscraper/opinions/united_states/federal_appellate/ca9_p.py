"""
History:
    - 2014-08-05: Updated by mlr because it was not working, however, in middle
      of update, site appeared to change. At first there were about five
      columns in the table and scraper was failing. Soon, there were seven and
      the scraper started working without my fixing it. Very odd.
    - 2023-01-13: Update to use RSS Feed
"""
from datetime import datetime

import feedparser
from lxml.html import tostring

from casemine.casemine_util import CasemineUtil
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ca9.uscourts.gov/opinions/index.xml"
        self.status = "Published"

    def _process_html(self) -> None:
        feed = feedparser.parse(tostring(self.html))
        for item in feed["entries"]:
            dockets = [item["link"].split("/")[-1][:-4]]
            self.cases.append(
                {
                    "name": titlecase(item["title"]),
                    "url": item["link"],
                    "date": item["published"],
                    "status": self.status,
                    "docket": dockets
                }
            )

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.parse()
        return 0

    def get_class_name(self):
        return "ca9_p"

    def get_court_name(self):
        return 'United States Court Of Appeals For The Ninth Circuit'

    def get_court_type(self):
        return 'Federal'
