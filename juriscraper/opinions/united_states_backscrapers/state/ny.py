"""
Scraper for New York Court of Appeals
CourtID: ny
Court Short Name: NY
History:
 2015-10-27  Created by Andrei Chelaru
"""
from datetime import date

from dateutil.rrule import DAILY, rrule

from juriscraper.opinions.united_states.state.nyappterm_1st import (
    Site as NySite,
)


class Site(NySite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interval = 200
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                DAILY,
                interval=self.interval,
                dtstart=date(2003, 6, 1),
                until=date(2016, 1, 1),
            )
        ]
        self.court = "Court of Appeals"
