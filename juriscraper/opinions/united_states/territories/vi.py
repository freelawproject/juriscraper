"""Scraper for Supreme Court of Virgin Islands
CourtID: vi
Court Short Name: Virgin Islands
Author: William Edward Palin
History:
  2023-01-21: Created by William Palin
"""
import urllib.parse
from datetime import date, datetime, timedelta

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            f"https://supreme.vicourts.org/court_opinions/published_opinions"
        )
        self.status = "Published"
        today = date.today()
        self.last_month = today - timedelta(days=30)

    def _process_html(self):
        if self.test_mode_enabled():
            self.last_month = datetime(2022, 12, 25).date()
        for s in self.html.xpath(".//tr/td/.."):
            cells = s.xpath(".//td")
            judges = cells[3].text_content()
            if not cells[0].text_content():
                continue
            dt = convert_date_string(cells[1].text_content())
            if dt < self.last_month:
                continue
            u = s.xpath(".//td/a/@href")[0]
            url = urllib.parse.quote(u, safe="/:")
            self.cases.append(
                {
                    "name": cells[0].text_content(),
                    "date": cells[1].text_content(),
                    "docket": cells[2].text_content(),
                    "judges": judges,
                    "url": url,
                }
            )
