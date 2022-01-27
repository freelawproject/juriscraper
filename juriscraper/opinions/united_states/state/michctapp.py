"""Scraper for the Michigan Court of Appeals
CourtID: michctapp
Court Short Name: Mich. Ct. App.
Type: Published and Unpublished
Reviewer: mlr
History:
    - 2014-09-19: Created by Jon Andersen
    - 2022-01-28: Updated for new web site, @satsuki-chan.
"""
import re
import time
from typing import List

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.opinions.united_states.state import mich


class Site(mich.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.courts.michigan.gov/api/CaseSearch/SearchCaseOpinions?resource=opinion&aAppellateCourt=Court%20Of%20Appeals&searchQuery=&sortOrder=Newest&page=1&pageSize=100"
        self.back_scrape_iterable = list(range(1, 999))

    def _process_html(self) -> None:
        for item in self.html["searchItems"]:
            title = item["title"]
            match = re.search(self.title_re, title)
            if not match:
                logger.warning(
                    f"Opinion '{title}' has no docket and case name."
                )
                continue
            docket = match.group("docket")
            name = self.get_name(match.group("name"))
            url = (
                f"https://www.courts.michigan.gov{item['documentUrl'].strip()}"
            )
            date = item["displayDate"]
            lower_courts = self.get_lower_courts(item["courts"])
            status = self.get_status(title)

            self.cases.append(
                {
                    "date": date,
                    "docket": docket,
                    "name": name,
                    "url": url,
                    "lower_courts": lower_courts,
                    "status": status,
                }
            )

    def get_status(self, title: str) -> str:
        if " Published" in title:
            status = "Published"
        else:
            status = "Unpublished"
        return status

    def _download_backwards(self, page: int) -> None:
        self.url = f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseOpinions?resource=opinion&aAppellateCourt=Court%20Of%20Appeals&searchQuery=&sortOrder=Newest&page={page}&pageSize=100"
        time.sleep(7)  # This site throttles if faster than 2 hits / 5s.
        self.html = self._download()
