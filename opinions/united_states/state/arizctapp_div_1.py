"""
Author: Deb Linton
Date created: 2014-02-14
Scraper for the Court of Appeals of Arizona, Division 1
CourtID: arizctapp
Court Short Name: Ariz. Ct. App.
"""

import time
from datetime import date

from juriscraper.GenericSite import GenericSite
from juriscraper.opinions.united_states.state import ariz
from juriscraper.lib.string_utils import titlecase


class Site(ariz.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.azcourts.gov/opinions/SearchOpinionsMemoDecs.aspx?court=998'