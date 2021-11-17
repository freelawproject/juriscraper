"""Scraper for Court of Appeals of Kentucky
CourtID: kyctapp
Court Short Name: Ky. Ct. App.
Contact: https://courts.ky.gov/aoc/technologyservices/Pages/ContactTS.aspx

"""

import re

from juriscraper.opinions.united_states.state import ky


class Site(ky.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.parameters[
            "index"
        ] = "*{aaa711b4d9721269574a3d848abb439b} Court of Appeals Opinions (1996+)"
        self.docket_number_regex = re.compile(
            r"(?P<year>\d{4})-(?P<court>[CA]{2})-(?P<number>\d+)"
        )
