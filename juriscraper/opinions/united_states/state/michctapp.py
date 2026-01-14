"""Scraper for the Michigan Court of Appeals
CourtID: michctapp
Court Short Name: Mich. Ct. App.
Type: Published and Unpublished
Reviewer: mlr
History:
    - 2014-09-19: Created by Jon Andersen
    - 2022-01-28: Updated for new web site, @satsuki-chan.
    - 2026-01-14: Updated for new secondary request url
"""

import re
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from juriscraper.opinions.united_states.state import mich


class Site(mich.Site):
    court = "Court Of Appeals"
    extract_from_text = OpinionSite.extract_from_text

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        params = self.filters + (("aAppellateCourt", self.court),)
        self.url = f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseOpinions?{urlencode(params)}"

    def get_missing_name_and_docket(self, item: dict) -> tuple[str, str]:
        """Try to get the case name using a secondary request

        Example of the content in the URL
        https://www.courts.michigan.gov/api/CaseSearch/SearchCaseSearchContent?searchQuery=371918

        :param item: the opinion item from the API
        :return: case name and docket number
        """
        if self.test_mode_enabled():
            return "Placeholder name", "Placeholder docket"

        logger.info("Getting case name from secondary request")
        if match := re.search(
            r"\d{7}_C(?P<docket_number>\d{6})", item["title"]
        ):
            docket_number = match.group("docket_number")
        else:
            docket_number = item["caseUrl"].split("/")[-1]

        if not docket_number:
            logger.error("michctapp: could not get docket number", extra=item)
            return "Placeholder name", "Placeholder docket"

        url = f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseSearchContent?searchQuery={docket_number}"
        self._request_url_get(url)
        response = self.request["response"].json()
        search_items = response.get("caseDetailResults", {}).get("searchItems", [])
        if not search_items:
            logger.error(f"michctapp: no results from search API for docket {docket_number}")
            return "Placeholder name", docket_number
        return self.cleanup_case_name(search_items[0]["title"]), docket_number

    def get_disposition(self, item: dict) -> str:
        """Get the disposition value

        Examples:
        Affirm in Part, Vacate in Part, Remanded
        L/Ct Judgment/Order Affirmed
        Appeal Dismissed

        :param item:
        :return: the disposition string
        """
        return (
            (item.get("decision", "") or "")
            .replace("L/Ct", "Lower Court")
            .strip()
        )
