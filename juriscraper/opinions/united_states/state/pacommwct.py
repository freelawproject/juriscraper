"""
Scraper for Pennsylvania Commonwealth Court
CourtID: pacomm
Court Short Name: pacomm
Author: Andrei Chelaru
Reviewer: mlr
Date created: 21 July 2014

If there are errors with this site, you can contact:

  Amanda Emerson
  717-255-1601

She's super responsive.
"""
from typing import Any, Dict

from juriscraper.opinions.united_states.state import pa


class Site(pa.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.pacourts.us/Rss/Opinions/Commonwealth/"
        self.set_regex(r"(.*)(?:- |et al.\s+)(\d+.*\d{4})")
        self.base = (
            "//item[not(contains(title/text(), 'Judgment List'))]"
            "[not(contains(title/text(), 'Reargument Table'))]"
            "[not(contains(title/text(), 'Order Amending Rules'))]"
        )

    def _get_precedential_statuses(self):
        return ["Unknown"] * len(self.cases)

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Can we extract the status from the text?

        The opinions contain OPINION at the start and don't contain NOT REPORTED
        meanwhile orders in the mix should just be labeled unpublished

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        if "OPINION NOT REPORTED" in scraped_text[:500]:
            status = "Unpublished"
        elif "OPINION" in scraped_text[:500]:
            status = "Published"
        else:
            status = "Unknown"
        metadata = {
            "OpinionCluster": {
                "precedential_status": status,
            },
        }
        return metadata
