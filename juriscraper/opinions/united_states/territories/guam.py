"""Scraper for Supreme Court of Guam
CourtID: guam
Court Short Name: Guam
Author: mmantel
History:
  2019-12-09: Created by mmantel
"""

import re
from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.guamsupremecourt.com/Supreme-Court-Opinions/Supreme-Court-Opinions.asp"
        self._year = date.today().year
        self.parameters = {"Year": str(self._year)}
        self.method = "POST"
        self.status = "Published"

        # The year dropdown goes back to 1990, but the Court wasn't
        # created until 1996 and there are no opinions posted for
        # prior years.
        self.back_scrape_iterable = range(1996, self._year)

    def _process_html(self):
        year = 2019 if self.test_mode_enabled() else self._year
        middle_of_year = "July 2, %d" % year

        for table in self.html.xpath(
            '//a[@id="Opinion"]/following-sibling::table'
        ):
            text = table.xpath(".//td/text()")[0]
            # Text is typically something like this:
            # CVA16-016, 2018 Guam 8, July 26, 2018
            # But formatting varies from year to year, and some elements
            # are not provided for some cases.

            date_match = re.search(r"[A-Za-z]+\.?\s+[0-9]+,\s+[0-9]+", text)
            docket_match = re.search(r"[A-Z]+[0-9]+\-+[0-9]+", text)
            neutral_citation_match = re.search(r"[0-9]+\s+Guam\s+[0-9]+", text)

            self.cases.append(
                {
                    "date": date_match.group(0)
                    if date_match
                    else middle_of_year,
                    "date_filed_is_approximate": date_match is None,
                    "docket": docket_match.group(0) if docket_match else "",
                    "name": table.xpath(".//a/text()")[0],
                    "citation": neutral_citation_match.group(0)
                    if neutral_citation_match
                    else "",
                    "url": table.xpath(".//a/@href")[0],
                }
            )

    def _download_backwards(self, year):
        self._year = year
        self.parameters = {"Year": str(year)}
        self.html = self._download()
        self._process_html()
