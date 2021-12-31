"""Scraper for Colorado Appeals Court
CourtID: coloctapp
Court Short Name: Colo. Ct. App.
"""

import re

from juriscraper.AbstractSite import logger
from juriscraper.opinions.united_states.state import colo


class Site(colo.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.courts.state.co.us/Courts/Court_Of_Appeals/Case_Announcements/Index.cfm"
        # self.base_path = "//div[@id='dnn_ctr2514_ModuleContent']/ul/li/a"
        # self.next_subpage_path = "//a[@id='dnn_ctr2517_DNNArticle_List_MyArticleList_MyPageNav_cmdNext']"
        self.status = "Unpublished"

    def _process_html(self) -> None:
        """Process HTML
        Iterate over each link found in the recent announcements list.
        If a valid URL link with citation and docket is not found, skip it

        Return: None
        """
        citation_docket_re = r".*(?P<citation>\d{4}\s+\w+\s+\d+)\s*–\s*(?P<docket>\w{5,8})(?P<name>.*)"
        date_text = self.html.xpath("//div[@id='main-content']//p[1]//text()")[
            0
        ]
        match = re.search(r"(?P<date>\w+ \d+, \d+).*", date_text)
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
            # - "21CA0738 People In Interest of A-D.M-F., a Child"
            # - "21CA1334 People In Interest of A.D.C., a Child"
            title = link.text_content()
            if not title:
                continue
            if title == date:
                # Skip link to this week's announcement file
                continue
            match = re.search(citation_docket_re, title)
            if not match:
                logger.info(
                    f"Unable to parse citation and docket from title: '{title}', case: '{str(link)}'"
                )
                continue
            citation = match.group("citation")
            docket = match.group("docket")
            name = match.group("name").strip()
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
