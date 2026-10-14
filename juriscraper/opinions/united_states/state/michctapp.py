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
from datetime import date, datetime
from typing import NotRequired
from urllib.parse import urlencode

from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import SiteOptions, logger
from juriscraper.ClusterSite import ClusterSite
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import OpinionType
from juriscraper.opinions.united_states.state import mich
from juriscraper.OpinionSite import OpinionSite


class _CaseTitle(TypedDict):
    title: str


class _CaseDetails(TypedDict):
    searchItems: NotRequired[list[_CaseTitle]]


class _Search(TypedDict):
    caseDetailResults: NotRequired[_CaseDetails]


_search_adapter = TypeAdapter(_Search)


class Site(ClusterSite[tuple[date, date]], mich.Site):
    court = "Court Of Appeals"
    first_opinion_date = datetime(1996, 4, 9)
    extract_from_text = OpinionSite.extract_from_text

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        params = self.filters + (("aAppellateCourt", self.court),)
        self.url = f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseOpinions?{urlencode(params)}"

    @override
    async def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        items = mich.SEARCH_RESPONSE.validate_python(self.html, strict=True)[
            "searchItems"
        ]
        for item in items:
            case_dict = await self._extract_case_data_from_item(item)

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
            if not bool(self.cluster_opinions(case_dict, self.cases)):
                self.cases.append(case_dict)

    @override
    async def get_missing_name_and_docket(
        self, item: mich.SearchItem
    ) -> tuple[str, str]:
        """Try to get the case name using a secondary request

        Example of the content in the URL
        https://www.courts.michigan.gov/api/CaseSearch/SearchCaseSearchContent?searchQuery=371918

        :param item: the opinion item from the API
        :return: case name and docket number
        """
        if self.test_mode_enabled():
            return "Placeholder name", "Placeholder docket"

        logger.info("Getting case name from secondary request")
        if (
            match := re.search(
                r"\d{7}_C(?P<docket_number>\d{6})", item["title"]
            )
        ) is not None:
            docket_number = match.group("docket_number")
        else:
            docket_number = item["caseUrl"].split("/")[-1]

        if not bool(docket_number):
            logger.error("michctapp: could not get docket number", extra=item)
            return "Placeholder name", "Placeholder docket"

        url = f"https://www.courts.michigan.gov/api/CaseSearch/SearchCaseSearchContent?searchQuery={docket_number}"
        await self._request_url_get(url)
        response = self.request.get("response")
        if response is None:
            raise ValueError("Download a response before accessing it.")
        response = _search_adapter.validate_python(
            response.json(), strict=True
        )
        search_items = response.get("caseDetailResults", {}).get(
            "searchItems", []
        )
        if not bool(search_items):
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

    @override
    def get_disposition(self, item: mich.SearchItem) -> str:
        """Get the disposition value

        Examples:
        Affirm in Part, Vacate in Part, Remanded
        L/Ct Judgment/Order Affirmed
        Appeal Dismissed

        :param item:
        :return: the disposition string
        """
        return (
            (
                decision_value
                if (decision_value := item.get("decision", "")) is not None
                else ""
            )
            .replace("L/Ct", "Lower Court")
            .strip()
        )
