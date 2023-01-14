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
"""

import re
from datetime import date

from juriscraper.lib.string_utils import normalize_dashes
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = date.today().strftime("%y")
        self.url = f"http://www.jud.ct.gov/external/supapp/archiveAROsup{self.year}.htm"
        self.status = "Published"
        self.cases = []
        self.docket_regex = r"SC\d+"

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        date = None
        for row in self.html.xpath(
            r"//*[re:match(text(), '.*\d{1,2}/\d{1,2}/\d{2,4}')] | //table[@id='AutoNumber1']//li",
            namespaces={"re": "http://exslt.org/regular-expressions"},
        ):
            dates = re.findall(r"\d{1,2}/\d{1,2}/\d{2,4}", row.text_content())
            if dates:
                date = dates[0]
                continue
            if not date:
                continue
            link_node = row.xpath(".//a")[0]
            link_text = link_node.text_content().strip()
            name = normalize_dashes(row.text_content().replace(link_text, ""))
            name = re.sub(r" - ", "", name).strip()
            dockets = ", ".join(re.findall(self.docket_regex, link_text))
            self.cases.append(
                {
                    "date": date,
                    "url": link_node.attrib["href"],
                    "docket": dockets,
                    "name": name,
                }
            )
