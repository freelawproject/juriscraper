"""
Scraper for Massachusetts Supreme Court
CourtID: mass
Court Short Name: MS
Author: Andrei Chelaru
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Reviewer: mlr
History:
 - 2014-07-12: Created.
 - 2014-08-05, mlr: Updated regex.
 - 2014-09-18, mlr: Updated regex.
 - 2016-09-19, arderyp: Updated regex.
 - 2017-11-29, arderyp: Moved from RSS source to HTML
    parsing due to website redesign
 - 2023-01-28, William Palin: Updated scraper
"""

import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    """
    Backscraper is implemented on `united_states_backscrapers.state.mass.py`
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.mass.gov/info-details/new-opinions"
        self.court_id = self.__module__
        self.court_identifier = "SJC"
        self.request.update({"headers": {}})
        self.needs_special_headers = True
        self.expected_content_types = ["application/pdf"]

    def _process_html(self):
        print(self.html)

        for row in self.html.xpath(".//a/@href[contains(.,'download')]/.."):
            url = row.get("href")
            content = row.text_content()
            m = re.search(r"(.*?) \((.*?)\)( \((.*?)\))?", content)
            if not m:
                continue
            name, docket, _, date = m.groups()
            if self.court_identifier not in docket:
                continue
            if date is None:
                # Likely a new case opinion - check the header text above it
                if row.xpath(".//../../h3/text()"):
                    header_text = row.xpath(".//../../h3/text()")[0]
                    date = header_text.split("Decisions:")[1].strip()
                if not date:
                    # if no date is found skip it
                    continue
            self.cases.append(
                {
                    "name": name,
                    "status": "Published",
                    "date": date,
                    "docket": docket,
                    "url": url,
                }
            )
