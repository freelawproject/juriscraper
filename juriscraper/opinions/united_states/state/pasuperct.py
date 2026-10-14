"""
Scraper for Pennsylvania Superior Court
CourtID: pasup
Court Short Name: pasup
Author: Andrei Chelaru
Reviewer: mlr
Date created: 21 July 2014
"""

import re
from datetime import date, datetime
from urllib.parse import urlencode

from typing_extensions import Unpack, override

from juriscraper.AbstractSite import SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import ExtractedMetadata
from juriscraper.opinions.united_states.state import pa


class Site(pa.Site):
    court = "Superior"
    first_opinion_date = datetime(1998, 2, 15)
    judge_key = "AuthorName"
    post_type_key = "PostingTypeCode"

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[tuple[date, date]]],
    ) -> None:
        """
        About the postTypes filter:
        1 = opinion
        2 = opinion per curiam
        3 = Opinion in Support of Affirmance
        4 = Opinion in Support of Reversal
        5 = Memorandum
        6 = Judgment Order
        7 = Concurring Opinion
        8 = Dissenting Opinion
        9 = Concurring and Dissenting Opinion
        10 = Concurring Statement
        11 = Dissenting Statement
        12 = Concurring and Dissenting Statement
        13 = Concurring Memorandum
        14 = Dissenting Memorandum
        15 = Concurring and Dissenting Memorandum
        16 = Concurring Memorandum Statement
        17 = Dissenting Memorandum Statement
        18 = Concurring and Dissenting Memorandum Statement
        19 = Per Curiam Order
        32 = Revised
        33 = Complete
        """
        super().__init__(cnt, user_agent, **kwargs)
        self.court_id = self.__module__
        self.params["postTypes"] = (
            "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,32,33"
        )
        self.url = f"{self.base_url}{urlencode(self.params)}"

    @override
    def get_status(self, op: pa.Posting) -> str:
        """Get status from opinion object

        :param op: opinion json
        :return: parsed status
        """
        publication_type = op.get("PublicationType")
        descr = (
            publication_type.get("Description")
            if publication_type is not None
            else None
        )
        if descr == "Non-Precedential":
            return "Unpublished"
        if descr == "Precedential":
            return "Published"
        return "Unknown"

    @override
    def clean_judge(self, author_str: str) -> str:
        """
        Examples:
        Input: "Wallace, J."
        Output: "Wallace"

        Input: "Leadbetter, President Judge Emerita"
        Output: "Leadbetter"

        Input: "Cohn Jubelirer, President Judge ~ Concurring and Dissenting Opinion by McCullough, J."
        Output: "Cohn Jubelirer; McCullough"
        """
        regex = r"(?P<judge>\w+\s*\w*),\s+(President|(P\.)?J\.)"
        match = re.finditer(regex, author_str)
        if bool(match):
            return ". ".join([m.group("judge") for m in match]).replace(
                " by ", " "
            )
        return author_str

    @override
    def extract_from_text(self, scraped_text: str) -> ExtractedMetadata:
        """Get neutral citation from the first lines in the first page

        Not all scraped opinions have them
        """
        neutral_citation_regex = r"\d{4} PA Super \d+"
        if (
            cite_match := re.search(neutral_citation_regex, scraped_text[:200])
        ) is not None:
            return {"Citation": cite_match.group(0)}

        return {}
