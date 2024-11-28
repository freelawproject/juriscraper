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

import re
from datetime import datetime
from urllib.parse import urlencode

from juriscraper.opinions.united_states.state import pasuperct
from juriscraper.OpinionSite import OpinionSite


class Site(pasuperct.Site):
    court = "Commonwealth"
    first_opinion_date = datetime(1998, 8, 17)
    # Deactivate extract_from_text from parent class
    # and avoid triggering the example requirement from
    # tests.local.test_ScraperExtractFromTextTest
    extract_from_text = OpinionSite.extract_from_text

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.regex = re.compile(r"(.*)(?:- |et al.\s+)(\d+.*\d{4})")
        self.params["postTypes"] = "complete,mo,opc,pn,sjo"
        self.url = f"{self.base_url}{urlencode(self.params)}"
