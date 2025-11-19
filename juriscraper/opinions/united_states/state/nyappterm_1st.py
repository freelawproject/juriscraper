# Scraper for New York Appellate Term 1st Dept.
# CourtID: nyappterm_1st
# Court Short Name: NY

import re
from datetime import date
from typing import Any

from juriscraper.lib.string_utils import clean_string
from juriscraper.opinions.united_states.state import ny


class Site(ny.Site):
    first_opinion_date = date(2003, 9, 25)

    # If more than 500 results are found, no results will be shown
    days_interval = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court = "Appellate Term, 1st Dept"
        self.court_id = self.__module__
        self._set_parameters()
        self.make_backscrape_iterable(kwargs)

    def extract_from_text(self, scraped_text: str) -> dict[str, Any]:
        """Can we extract the docket number from the text?

        Examples
        2017-1270 K CR
        570086/18
        20-159

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        regexes = [
            re.compile(
                r"<br>[\s\n]*(?P<docket_number>\d{2,}-\d{2,}( [A-Z]{1,2} CR?)?)"
            ),
            re.compile(r"<br>[\s\n]*(?P<docket_number>\d+/\d+)[\s\n]*<br>"),
        ]
        for regex in regexes:
            if match := regex.search(clean_string(scraped_text[:2500])):
                cleaned_docket = self.clean_docket_match(match)
                if cleaned_docket:
                    return {"Docket": {"docket_number": cleaned_docket}}

        return {}
