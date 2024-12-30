"""
Scraper for New York Court of Appeals
CourtID: ny
Court Short Name: NY
History:
 2015-10-27  Created by Andrei Chelaru
"""

from datetime import date

from juriscraper.opinions.united_states.state.nyappterm_1st import (
    Site as NySite,
)


class Site(NySite):
    first_opinion_date = date(2003, 10, 27)
    days_interval = 180

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court = "Court of Appeals"
