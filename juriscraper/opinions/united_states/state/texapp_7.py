# Scraper for Texas 7th Court of Appeals
# CourtID: texapp7
# Court Short Name: TX
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-10
from juriscraper.opinions.united_states.state import tex


class Site(tex.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "capp_7"
        self.checkbox = 8

    def make_case_name_short(self, s):

        """Creates short case names where obvious ones can easily be made."""
        parts = [part.strip().split() for part in s.split(" v. ")]
        if len(parts) == 1:
            # No v. Likely an "In re" or "Matter of" case.
            if len(parts[0]) <= 3:
                # Good length for a shortened case name.
                return s
            else:
                # Too long; too weird. Punt.
                return ""
    def get_court_name(self):
        return "Texas Court of Appeals"

    def get_class_name(self):
        return "texapp_7"
