"""
Scraper for Pennsylvania Superior Court
CourtID: pasup
Court Short Name: pasup
Author: Andrei Chelaru
Reviewer: mlr
Date created: 21 July 2014
"""

import re
from datetime import datetime
from typing import Dict
from urllib.parse import urlencode

from juriscraper.opinions.united_states.state import pa


class Site(pa.Site):
    court = "Superior"
    first_opinion_date = datetime(1998, 2, 15)
    judge_key = "AuthorName"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.params["postTypes"] = (
            "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,32,33"
        )
        self.url = f"{self.base_url}{urlencode(self.params)}"

    def get_status(self, op: Dict) -> str:
        """Get status from opinion object

        :param op: opinion json
        :return: parsed status
        """
        descr = op.get("PublicationType", {}).get("Description", "")
        if descr == "Non-Precedential":
            return "Unpublished"
        if descr == "Precedential":
            return "Published"
        return "Unknown"

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
        if match:
            return ". ".join([m.group("judge") for m in match]).replace(
                " by ", " "
            )
        return author_str

    def extract_from_text(self, scraped_text: str) -> Dict:
        """Get neutral citation from the first lines in the first page

        Not all scraped opinions have them
        """
        neutral_citation_regex = r"\d{4} PA Super \d+"
        if cite_match := re.search(neutral_citation_regex, scraped_text[:200]):
            return {"Citation": cite_match.group(0)}

        return {}
