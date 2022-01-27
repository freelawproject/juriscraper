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
        """Process HTML
        Iterate over each opinion item in the JSON response.
        If an item's title does not have a docket and the case's name, skip it.

        Return: None
        """
        title_re = r"COA (?P<docket>\d+)\s+(?P<name>.+)\s+Opinion"
        for item in self.html["searchItems"]:
            title = item["title"]
            match = re.search(title_re, title)
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
        """Get opinion's status
        If the title's of an opinion includes the word "Published", then the document has that precential status. Unpublished documents include the word "Unpublished" or omit the status in the title.
        Examples:
            - "COA 353302 PEOPLE OF MI V DWIGHT T SAMUELS Opinion - Authored - Published 12/27/2021"
            - "COA 356839 IN RE VARNADO MINORS Opinion - Per Curiam - Unpublished 12/27/2021"
            - "COA 354223 C LOTUS SMITH V HENRY FORD HEALTH SYSTEM Opinion - Concurrence 12/27/2021"
            - "COA 356970 P IN RE JAMES YANG Opinion - Partial Concurrence/Dissent 12/27/2021"

        Return: String
        """
        if "Published" in title:
            status = "Published"
        else:
            status = "Unpublished"
        return status

    def _download_backwards(self, page: int) -> None:
        self.url = f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseOpinions?resource=opinion&aAppellateCourt=Court%20Of%20Appeals&searchQuery=&sortOrder=Newest&page={page}&pageSize=100"
        time.sleep(7)  # This site throttles if faster than 2 hits / 5s.
        self.html = self._download()
