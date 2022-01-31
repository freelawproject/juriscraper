"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Philip Ardery
Reviewer: mlr
Date created: 2016-06-03
Contact: Email "Internet and Technology" staff listed at http://www.cobar.org/staff
         they usually fix issues without resonding to the emails directly. You can
         also try submitting the form here: http://www.cobar.org/contact
History:
    - 2022-01-31: Updated by William E. Palin
"""

import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.courts.state.co.us/Courts/Supreme_Court/Case_Announcements/"

    def _process_html(self) -> None:

        date = self.html.xpath(
            ".//p[contains(text(), 'case announcements for')]/text()"
        )[0]
        date_str = (
            re.findall(r"case announcements for (.*) are now", date)[0]
            .split(",", 1)[1]
            .strip()
        )
        for item in self.html.xpath(
            ".//a[contains(@href, 'Supreme_Court/Opinions/')]"
        ):
            docket, name = item.text_content().split(" ", 1)
            self.cases.append(
                {
                    "date": date_str,
                    "docket": docket,
                    "name": name,
                    "url": item.attrib["href"],
                    "status": "Published",
                }
            )
