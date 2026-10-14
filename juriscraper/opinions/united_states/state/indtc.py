"""
Scraper for Indiana Tax Court
CourtID: indtc
Court Short Name: Ind. Tax.
Auth: Jon Andersen <janderse@gmail.com>
Reviewer: mlr
History:
    2014-09-03: Created by Jon Andersen
"""

import re

from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.opinions.united_states.state import ind


class Site(ind.Site):
    page_court_id = "9550"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.court_name = "Tax Court"
        self.status = "Unknown"

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Extract publication status

        :param scraped_text: Text of scraped content
        :return: metadata
        """
        if bool(re.findall(r"\bNOT FOR PUBLICATION\b", scraped_text)):
            status = "Unpublished"
        elif bool(re.findall(r"\bFOR PUBLICATION\b", scraped_text)):
            status = "Published"
        else:
            status = "Unknown"
        metadata: ExtractedMetadata = {
            "OpinionCluster": {
                "precedential_status": status,
            },
        }
        return metadata
