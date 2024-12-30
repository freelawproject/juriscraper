# Scraper for New York Appellate Divisions 1st Dept.
# CourtID: nyappdiv_1st
# Court Short Name: NY
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-04
import re
from datetime import date
from typing import Any, Dict

from juriscraper.opinions.united_states.state import ny


class Site(ny.Site):
    first_opinion_date = date(2003, 9, 25)
    days_interval = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "App Div, 1st Dept"
        self.make_backscrape_iterable(kwargs)
        self._set_parameters()

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Can we extract the docket number from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        dockets = re.search(
            r"^<br>(?P<docket_number>(Docket|Index|Ind\.|Motion|SCI) No\..* Case No\..*)\s+?$",
            scraped_text[:2000],
            re.MULTILINE,
        )
        if dockets:
            return {"Docket": dockets.groupdict()}
        return {}
