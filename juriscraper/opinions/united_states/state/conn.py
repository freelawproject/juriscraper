"""Scraper for Connecticut Supreme Court
CourtID: conn
Court Short Name: Conn.
Author: Asadullah Baig <asadullahbeg@outlook.com>
History:
    - 2014-07-11: created
    - 2014-08-08, mlr: updated to fix InsanityError on case_dates
    - 2014-09-18, mlr: updated XPath to fix InsanityError on docket_numbers
    - 2015-06-17, mlr: made it more lenient about date formatting
    - 2016-07-21, arderyp: fixed to handle altered site format
    - 2017-01-10, arderyp: restructured to handle new format use case that includes opinions without dates and flagged for 'future' publication
    - 2022-02-02, satsuki-chan: Fixed docket and name separator, changed super class to OpinionSiteLinear
    - 2023-11-04, flooie: Fix scraper
"""

import re
from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = date.today().strftime("%y")
        self.url = f"http://www.jud.ct.gov/external/supapp/archiveAROsup{self.year}.htm"
        self.status = "Published"

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        for row in self.html.xpath("//ul/preceding-sibling::p"):
            if "Published in the Law Journal" not in row.text_content():
                continue
            date = row.text_content().split(" ")[-1][:-1]
            for document in row.xpath("following-sibling::ul[1]/li"):
                output_string = re.sub(
                    r"\s{2,}", " ", document.text_content()
                ).strip()
                name = output_string.split("-")[-1].strip()
                docket = document.xpath(".//a")[0].text_content().split()[0]
                self.cases.append(
                    {
                        "date": date,
                        "url": document.xpath(".//a")[0].get("href"),
                        "docket": docket,
                        "name": name,
                    }
                )
