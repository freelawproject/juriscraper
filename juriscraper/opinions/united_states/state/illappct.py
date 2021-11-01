# -*- coding: utf-8 -*-
"""
# Author: Krist Jin
# 2013-08-18: Created.
# 2014-07-17: Updated by mlr to remedy InsanityException.
"""

from juriscraper.opinions.united_states.state import ill
from juriscraper.AbstractSite import logger
import re


class Site(ill.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.illinoiscourts.gov/top-level-opinions?type=appellate"
        )

    def extract_docket(self, case_citation):
        # RegEx: "[{YYYY: year_4_digit}|] IL [App|] ({d: appellate district}[st|d|th]) {docket_number}[-U|]"
        search = re.search(r"(?:.+\()(\d+)(?:.+\)\s+)(\d+)", case_citation)
        if search:
            district = search.group(1)
            docket = search.group(2)
            docket = f"{district}-{docket[0:2]}-{docket[2:]}"
        else:
            district = ""
            docket = ""
            logger.warning(f"Docket not found: {case_citation}")
        return docket
