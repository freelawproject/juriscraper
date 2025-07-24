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

from juriscraper.opinions.united_states.state import ind


class Site(ind.Site):
    page_court_id = "9550"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "Tax Court"
        self.status = "Unknown"

    def extract_from_text(self, scraped_text: str):
        """Extract publication status

        :param scraped_text: Text of scraped content
        :return: metadata
        """
        if re.findall(r"\bNOT FOR PUBLICATION\b", scraped_text):
            status = "Unpublished"
        elif re.findall(r"\bFOR PUBLICATION\b", scraped_text):
            status = "Published"
        else:
            status = "Unknown"
        metadata = {
            "OpinionCluster": {
                "precedential_status": status,
            },
        }
        return metadata
