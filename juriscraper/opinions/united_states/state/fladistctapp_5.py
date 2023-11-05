"""
Scraper for Florida 5th District Court of Appeal
CourtID: flaapp5
Court Short Name: flaapp5
Court Contact: 5dca@flcourts.org, 386-947-1530
Author: Andrei Chelaru
Reviewer: mlr
History:
 - 2014-07-23, Andrei Chelaru: Created.
 - 2014-08-05, mlr: Updated.
 - 2014-08-06, mlr: Updated.
 - 2014-09-18, mlr: Updated date parsing code to handle Sept.
 - 2016-03-16, arderyp: Updated to return proper absolute pdf url paths, simplify date logic
"""

import re

from lxml import html

from juriscraper.lib.string_utils import (
    clean_string,
    convert_date_string,
    normalize_dashes,
)
from juriscraper.OpinionSite import OpinionSite

from . import fladistctapp


class Site(fladistctapp.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.number = "fifth"
        self.base = "https://5dca.flcourts.gov"
        self.update_url()
