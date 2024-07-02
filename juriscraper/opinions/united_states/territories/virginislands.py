"""Scraper for Supreme Court of Virgin Islands
CourtID: virginislands
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
        self.previous_date = today - timedelta(days=60)

    def _process_html(self):
        if self.test_mode_enabled():
            self.previous_date = datetime(2023, 9, 21).date()

        for s in self.html.xpath(".//tr/td/.."):
            cells = s.xpath(".//td")
            if not cells[0].text_content():
                continue

            judges = cells[3].text_content()
            name = cells[0].text_content()
            date = cells[1].text_content().replace("/", "-")
            date_object = convert_date_string(date)
            docket = cells[2].text_content()
            citation = cells[4].text_content()
            if date_object < self.previous_date:
                continue
            u = s.xpath(".//td/a/@href")[0]
            url = urllib.parse.quote(u, safe="/:")
            self.cases.append(
                {
                    "name": name,
                    "date": date,
                    "docket": docket,
                    "citation": citation,
                    "judges": judges,
                    "url": url,
                }
            )
