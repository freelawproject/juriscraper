"""Scraper for the Michigan Court of Appeals
CourtID: michctapp
Court Short Name: Mich. Ct. App.
Type: Published and Unpublished
Reviewer: mlr
History:
    - 2014-09-19: Created by Jon Andersen
    - 2022-01-28: Updated for new web site, @satsuki-chan.
"""
from typing import List
from urllib.parse import urlencode

from juriscraper.opinions.united_states.state import mich


class Site(mich.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "Court Of Appeals"
        params = self.filters + (("aAppellateCourt", self.court),)
        self.url = f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseOpinions?{urlencode(params)}"

    def _get_precedential_statuses(self) -> List[str]:
        """Find Precedential Status

        If the case is published they note Published in the title string.

        :return: Precedential statuses
        """
        for case in self.cases:
            case["precedential_status"] = self.get_status(case["title"])
        return [case["precedential_status"] for case in self.cases]

    def get_status(self, title: str) -> str:
        """Get the status of a case

        :param title: The JSON API title string
        :return: The status of the case
        """
        if "Published" in title:
            status = "Published"
        else:
            status = "Unpublished"
        return status
