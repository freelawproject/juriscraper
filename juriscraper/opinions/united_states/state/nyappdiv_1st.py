# Scraper for New York Appellate Divisions 1st Dept.
# CourtID: nyappdiv_1st
# Court Short Name: NY
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-04
import re
from datetime import date
from typing import Any

from juriscraper.lib.string_utils import clean_string
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

    def extract_from_text(self, scraped_text: str) -> dict[str, Any]:
        """Can we extract the docket number from the text?

        First group: explicitly named number (group).
        Some may be separated by '|', some by newlines, some may not have extra
        separation

        Examples:
        Index No. 650082/21|Appeal No. 5048-5049-5050|Case No. 2024-00406, 2024-02296, 2024-04014, 2024-07940|
        Motion No. 2025-00147|Case No. 2025-00150|
        Ind No. 1138/21|Appeal No. 4802|Case No. 2022-03304|
        Docket No. NN-01571/25
        SCI No. 3143/18|Appeal No. 4944|Case No. 2019-03817|

        Second group: implicit docket_number (group)
        Examples:

        KA 23-00823, KA 23-00932, KA 23-00933, KA 23-00934, AND KA 23-00935
        909 CAF 23-01991
        MOTION NO. (419/24) CA 23-00179.
        654 CA 24-01116
        M-4988 M-8
        KA 23-00947.
        712 TP 24-00718

        :param scraped_text: The content of the document downloaded
        :return: Metadata to be added to the case
        """
        regexes = [
            re.compile(
                r"<br>[\s\n]*(?P<docket_number>(\(?(Appeal|Docket|Index|Ind\.?|Motion|SCI|Case) No\.? [\d ,/A-Z&\[\]-]*\d[\d ,/A-Z&\[\]-]*[\s\n|<br>)]*)+)[\s\n]*<br>",
                flags=re.IGNORECASE,
            ),
            re.compile(
                r"<br>[\s\n]*(?P<docket_number>[A-Z0-9()/., -]*\d[A-Z0-9()/., -]*)[\s\n]*(<br>|DECISION, ORDER)"
            ),
        ]
        for regex in regexes:
            docket_match = regex.search(
                # use clean_string to normalize html escaped values like '&amp;'
                clean_string(scraped_text[:2500])
            )

            if docket_match:
                cleaned_docket = self.clean_docket_match(docket_match)
                if cleaned_docket:
                    return {"Docket": {"docket_number": cleaned_docket}}

        return {}
