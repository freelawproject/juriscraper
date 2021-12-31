"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Philip Ardery
Reviewer: mlr
Date created: 2016-06-03
Contact: Email "Internet and Technology" staff listed at http://www.cobar.org/staff
         they usually fix issues without resonding to the emails directly. You can
         also try submitting the form here: http://www.cobar.org/contact
"""

import re

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.courts.state.co.us/Courts/Supreme_Court/Case_Announcements/Index.cfm"
        self.status = "Published"

    def _process_html(self) -> None:
        """Process HTML
        Iterate over each link found in the recent announcements list.
        If a valid URL link with citation and docket is not found, skip it

        Return: None
        """
        citation_docket_re = r".*(?P<citation>\d{4}\s+\w+\s+\d+)\s*–\s*(?P<docket>\w{5,8})(?P<name>.*)"
        date_text = self.html.xpath("//div[@id='main-content']//p[1]/text()")[
            0
        ]
        match = re.search(r".*,\s+(?P<date>\w+ \d+, \d+),.*", date_text)
        if not match:
            logger.error(
                f"Unable to find date from announcements page: '{str(date_text)}'"
            )
            return
        date = match.group("date")

        for link in self.html.xpath(
            "//div[@id='main-content']//p/a[contains(@href, '.pdf')]"
        ):
            # Expected title content:
            # - "**2021 CO 82 – 21SA55, In Re Ronquillo v. EcoClean"
            # - "2021 CO 84 – 20SC236, Thomas v. People"
            title = link.text_content()
            if not title:
                continue
            match = re.search(citation_docket_re, title)
            if not match:
                logger.info(
                    f"Unable to parse citation and docket from title: '{title}', case: '{str(link)}'"
                )
                continue
            citation = match.group("citation")
            docket = match.group("docket")
            name = match.group("name").strip(" ,")
            url = link.get("href")
            self.cases.append(
                {
                    "date": date,
                    "docket": docket,
                    "name": name,
                    "neutral_citation": citation,
                    "url": url,
                }
            )
