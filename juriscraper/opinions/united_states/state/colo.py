"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Philip Ardery
Reviewer: mlr
Date created: 2016-06-03
Contact: Email "Internet and Technology" staff listed at http://www.cobar.org/staff
    they usually fix issues without responding to the emails directly. You can
    also try submitting the form here: http://www.cobar.org/contact
History:
    - 2022-01-31: Updated by William E. Palin
    - 2022-02-18: Date validation, regexp. improvements and extract_from_text, @satsuki-chan
"""

import re
from typing import Any, Dict

from juriscraper.lib.string_utils import normalize_dashes
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.courts.state.co.us/Courts/Supreme_Court/Case_Announcements/"

    def _process_html(self) -> None:
        date = self.html.xpath(
            ".//p[contains(text(), 'case announcements for')]/text()"
        )
        if date:
            date_str = (
                re.findall(r"case announcements for (.*) are now", date[0])[0]
                .split(",", 1)[1]
                .strip()
            )
            for item in self.html.xpath(
                ".//a[contains(@href, 'Supreme_Court/Opinions/')]"
            ):
                link_text = normalize_dashes(item.text_content().strip())
                cite_match = re.findall(r"(\d{2,4}\s*CO\s*\d+\w?)", link_text)
                docket_match = re.findall(r"\d+[A-Z]+\d{2,}", link_text)
                docket = docket_match[0] if docket_match else ""
                citation = cite_match[0] if cite_match else ""
                name = (
                    link_text.replace(docket, "")
                    .replace(citation, "")
                    .lstrip(",- ")
                )
                self.cases.append(
                    {
                        "date": date_str,
                        "docket": docket,
                        "name": name,
                        "url": item.attrib["href"],
                        "status": "Published",
                        "citation": citation,
                    }
                )

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Pass scraped text into function and return data as a dictionary
        Notes for 'Citation':
            - Reporter key for this court: 'CO'
            - Type for a state: 2
        :param scraped_text: Text of scraped content
        :return: metadata
        """
        match_re = r"The Supreme Court of the State of Colorado.*?(?P<citation>\d{4}\s*CO\s*\d+).*?Supreme Court Case No\. (?P<docket>\d+S[A-Z]\d+)"
        match = re.findall(match_re, scraped_text, re.M | re.S)
        if not match:
            metadata = {}
        else:
            volume, page = match[0][0].split("CO")
            metadata = {
                "OpinionCluster": {
                    "docket_number": match[0][1],
                },
                "Citation": {
                    "volume": volume.strip(),
                    "reporter": "CO",
                    "page": page.strip(),
                    "type": 2,
                },
            }
        return metadata
