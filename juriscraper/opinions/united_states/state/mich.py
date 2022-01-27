"""Scraper for the Supreme Court of Michigan
CourtID: mich
Court Short Name: Mich.
Contact: sitefeedback@courts.mi.gov
History:
    - 2014-09-21: Updated by Jon Andersen to handle some fields being missing
    - 2014-08-05: Updated to have a dynamic URL, an oversight during check in.
    - 2022-01-28: Updated for new web site, @satsuki-chan.
"""
import re
import time
from typing import List

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.courts.michigan.gov/api/CaseSearch/SearchCaseOpinions?resource=supreme-court-opinion&aAppellateCourt=Supreme%20Court&searchQuery=&sortOrder=Newest&page=1&pageSize=100"
        self.back_scrape_iterable = list(range(1, 99))
        self.request["headers"] = {"User-Agent": ""}
        self.title_re = (
            r"(MSC|COA) (?P<docket>\d+)\s+(?P<name>.+)\s+(Opinion|Order)"
        )
        self.status = "Published"
        self.cases = []

    def _process_html(self) -> None:
        for item in self.html["searchItems"]:
            match = re.search(self.title_re, item["title"])
            if not match:
                logger.warning(
                    f"Opinion '{item['title']}' has no docket and case name."
                )
                continue
            docket = match.group("docket")
            name = self.get_name(match.group("name"))
            url = (
                f"https://www.courts.michigan.gov{item['documentUrl'].strip()}"
            )
            date = item["displayDate"]
            lower_courts = self.get_lower_courts(item["courts"])

            self.cases.append(
                {
                    "date": date,
                    "docket": docket,
                    "name": name,
                    "url": url,
                    "lower_courts": lower_courts,
                }
            )

    def get_name(self, name_raw: str) -> str:
        name = titlecase(name_raw)
        if "People of Mi " in name:
            name = name.replace("People of Mi ", "People of Michigan ")
        return name

    def get_lower_courts(self, courts: List[str]) -> str:
        if courts:
            lower_courts = ", ".join(courts).lstrip(", ")
        else:
            lower_courts = ""
        return titlecase(lower_courts)

    def _get_lower_courts(self) -> List[str]:
        return self._get_optional_field_by_id("lower_courts")

    def _download_backwards(self, page: int) -> None:
        self.url = f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseOpinions?resource=supreme-court-opinion&aAppellateCourt=Supreme%20Court&searchQuery=&sortOrder=Newest&page={page}&pageSize=100"
        time.sleep(7)  # This site throttles if faster than 2 hits / 5s.
        self.html = self._download()
