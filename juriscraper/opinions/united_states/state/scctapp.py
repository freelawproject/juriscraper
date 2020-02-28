"""Scraper for South Carolina Supreme Court
CourtID: scctapp
Court Short Name: S.C. Ct. App.
Author: Varun Iyer
History:
 - 07-23-2018: Created.
"""

import datetime

from juriscraper.opinions.united_states.state import sc


class Site(sc.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        today = datetime.date.today()
        self.url = (
            "http://www.sccourts.org/opinions/indexCOAPub.cfm?year=%d&month=%d"
            % (today.year, today.month)
        )
        self.court_id = self.__module__
        self.court_name = "sctapp"
