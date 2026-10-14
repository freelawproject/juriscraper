"""Scraper for U.S. Merit Systems Protection Board
CourtID: mspb
Court Short Name: MSPB
Author: Jon Andersen
Reviewer: mlr
Date created: 1 Sep 2014
Type: Precedential
"""

import json

from pydantic import TypeAdapter
from typing_extensions import TypedDict, Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class _Opinion(TypedDict):
    FILE_NAME: str
    APL_FIRST_NAME: str
    APL_LAST_NAME: str
    AGENCY: str
    DECISION_NUMBER: str
    DOCKET_NBR: str
    ISSUED_DATE: str


class _Search(TypedDict):
    data: list[_Opinion]


_search_adapter = TypeAdapter(_Search)


class Site(OpinionSiteLinear):
    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://www.mspb.gov/decisions/precedential/PrecedentialDecisions_Manifest_Table.json"
        self.base = "https://www.mspb.gov/decisions/precedential"
        self.should_have_results = True

    @override
    def _process_html(self) -> None:
        if self.test_mode_enabled():
            with open(self.mock_url) as file:
                self.html = json.load(file)
        response = _search_adapter.validate_python(self.html, strict=True)
        for row in response["data"]:
            url = row["FILE_NAME"]
            name = f"{row['APL_FIRST_NAME']} {row['APL_LAST_NAME']} v. {row['AGENCY']}"
            self.cases.append(
                {
                    "citation": row["DECISION_NUMBER"],
                    "url": f"{self.base}/{url}",
                    "docket": row["DOCKET_NBR"],
                    "name": name,
                    "date": row["ISSUED_DATE"].replace("/", "-"),
                }
            )
