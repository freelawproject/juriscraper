"""Scraper for the Michigan Court of Appeals
CourtID: michctapp
Court Short Name: Mich. Ct. App.
Type: Published and Unpublished
Reviewer: mlr
History:
    - 2014-09-19: Created by Jon Andersen
    - 2022-01-28: Updated for new web site, @satsuki-chan.
    - 2026-01-14: Updated for new secondary request url
    - 2026-02-25: Added backscraping support going back to December 2000.
"""

import re
from datetime import datetime
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.ClusterSite import ClusterSite
from juriscraper.lib.type_utils import OpinionType
from juriscraper.opinions.united_states.state import mich
from juriscraper.OpinionSite import OpinionSite


class Site(ClusterSite, mich.Site):
    court = "Court Of Appeals"
    first_opinion_date = datetime(1996, 4, 9)
    extract_from_text = OpinionSite.extract_from_text

    def _check_sanity(self) -> None:
        """Like ClusterSite._check_sanity, but allows two MAJORITY opinions
        in a cluster.

        Michigan courts occasionally issue a substituted majority opinion
        alongside the original, both typed as MAJORITY. The substituted one
        is identified by its 'asv.pdf' suffix.
        """
        reclassified = []
        for case in self.cases:
            sub_opinions = case.get("sub_opinions", [])
            majority_ops = [
                op
                for op in sub_opinions
                if op.get("types") == OpinionType.MAJORITY.value
            ]

            # there could be more than 1 Advance Sheets Version (ASV)
            if len(majority_ops) >= 2:
                for op in majority_ops:
                    if (
                        op.get("download_urls")
                        .lower()
                        .endswith("asv.pdf")
                    ):
                        op["types"] = OpinionType.ADDENDUM.value
                        reclassified.append(op)

        try:
            super()._check_sanity()
        finally:
            for op in reclassified:
                op["types"] = OpinionType.MAJORITY.value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        params = self.filters + (("aAppellateCourt", self.court),)
        self.url = f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseOpinions?{urlencode(params)}"

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        for item in self.html["searchItems"]:
            case_dict = self._extract_case_data_from_item(item)

            # Use URL suffix to get the type. Other prefixes not used here
            # "o.opn.pdf": "On Remand" opinions
            # "a.opn.pdf": "After Second Remand"
            url = case_dict.get("url", "")
            lower_url = url.lower()
            if lower_url.endswith("p.opn.pdf"):
                case_dict["type"] = (
                    OpinionType.CONCURRING_IN_PART_AND_DISSENTING_IN_PART.value
                )
            elif lower_url.endswith("d.opn.pdf"):
                case_dict["type"] = OpinionType.DISSENT.value
            elif lower_url.endswith("c.opn.pdf"):
                case_dict["type"] = OpinionType.CONCURRENCE.value
            else:
                case_dict["type"] = OpinionType.MAJORITY.value

            # If we can't cluster it, append it to self.cases
            # if it was clustered, the data will already be in self.cases
            if not self.cluster_opinions(case_dict, self.cases):
                self.cases.append(case_dict)

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
        search_items = response.get("caseDetailResults", {}).get(
            "searchItems", []
        )
        if not search_items:
            logger.error(
                "michctapp: no results from search API for docket %s "
                % docket_number,
                extra={"search_items": search_items},
            )
            return "Placeholder name", docket_number
        elif len(search_items) > 1:
            logger.error(
                "michctapp: more than 1 from search API for docket %s "
                % docket_number,
                extra={"search_items": search_items},
            )
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
