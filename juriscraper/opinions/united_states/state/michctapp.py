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
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.opinions.united_states.state import mich


class Site(mich.Site):
    court = "Court Of Appeals"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        params = self.filters + (("aAppellateCourt", self.court),)
        self.url = f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseOpinions?{urlencode(params)}"

    def get_missing_name_and_docket(self, item: dict) -> tuple[str, str]:
        """Try to get the case name using a secondary request

        Example of the content in the URL
        https://www.courts.michigan.gov/c/courts/getcourtofappealscasedetaildata/377920

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

        url = f"https://www.courts.michigan.gov/c/courts/getcourtofappealscasedetaildata/{docket_number}"
        self._request_url_get(url)
        response = self.request["response"].json()

        if "error" in response:
            logger.warning(
                "michctapp: secondary request returned error: %s",
                response["error"],
            )
            return "Placeholder name", docket_number

        return self.cleanup_case_name(response["title"]), docket_number

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

    def extract_from_text(self, scraped_text: str) -> dict:
        """Extract case name and docket number from opinion text

        :param scraped_text: Text content of the opinion
        :return: Dictionary with extracted case name and docket number
        """
        case_pattern = re.compile(
            r"COURT OF APPEALS\s+"
            r"(?P<plaintiff>[A-Z][A-Z\s]+?),.*?"
            r"Plaintiff.*?"
            r"v\s+.*?No\.\s*(?P<docket>\d{6}).*?"
            r"(?P<defendant>[A-Z][A-Z\s]+?),.*?"
            r"Defendant",
            re.DOTALL,
        )
        if match := case_pattern.search(scraped_text[:2000]):
            plaintiff = self.cleanup_case_name(match.group("plaintiff"))
            defendant = self.cleanup_case_name(match.group("defendant"))
            docket_number = match.group("docket")
            case_name = f"{plaintiff} v. {defendant}"
            return {
                "OpinionCluster": {"case_name": case_name},
                "Docket": {"case_name": case_name, "docket_number": docket_number},
            }

        logger.warning(
            "michctapp: extract_from_text failed to match case pattern"
        )
        return {}
