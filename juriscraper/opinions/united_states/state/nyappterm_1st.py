# Scraper for New York Appellate Term 1st Dept.
# CourtID: nyappterm_1st
# Court Short Name: NY

import re
from datetime import date
from typing import Any, Dict

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

    def extract_from_text(self, scraped_text: str) -> Dict[str, Any]:
        """Can we extract the docket number from the text?

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        # Ny App Term 1st Dept. 2nd and Sup Ct all have different varying
        # docket number types.
        # ie. 123413/03 vs. 51706 vs. 2003-718 Q C or 2003-1288 K C

        dockets = re.findall(
            r"(\d+\/\d+)|^(\d{5,})|^(\d+-\d+ \w+\s\w+)", scraped_text
        )
        dockets = [list(filter(None, x)) for x in dockets]
        metadata = {
            "Docket": {
                "docket_number": dockets[0][0] if dockets else "",
            },
        }
        return metadata
