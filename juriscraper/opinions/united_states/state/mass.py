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

import datetime
import re
from datetime import datetime

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.mass.gov/service-details/new-opinions"
        self.court_id = self.__module__
        self.court_identifier = "SJC"

    def _process_html(self):
        for file in self.html.xpath(".//a/@href[contains(.,'pdf')]/.."):
            content = file.text_content()
            m = re.search(r"(.*?) \((.*?)\)( \((.*?)\))?", content)
            name, docket, _, date = m.groups()
            if self.court_identifier not in docket:
                continue
            url = file.get("href")
            parts = url.split("/")[-4:-1]
            parts = [int(d) for d in parts]
            date = datetime(year=parts[0], month=parts[1], day=parts[2]).date()
            self.cases.append(
                {
                    "name": name,
                    "status": "Published",
                    "date": str(date),
                    "docket": docket,
                    "url": url,
                }
            )
