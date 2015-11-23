"""Scraper for Mississippi Court of Appeals
CourtID: missctapp
Court Short Name: Miss. Ct. App.
Author: Jon Andersen
Reviewer: mlr
Type: Precedential
History:
    2014-09-21: Created by Jon Andersen
"""

from datetime import date

from juriscraper.opinions.united_states.state import miss
from lxml import html


class Site(miss.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__

        # If it's the beginning of January, we need to make sure that we aren't
        # missing any late-coming cases from the previous year.
        today = date.today()
        self.url = ('http://courts.ms.gov/scripts/websiteX_cgi.exe/GetOpinion?'
                    'Year={year}&Court=Court+of+Appeals&Submit=Submit').format(
                        year=int(today.year) - 1
                    )
        beginning_of_year = (
            date(today.year, 1, 1) <= today <= date(today.year, 1, 15))
        if not beginning_of_year:
            # This simply aborts the crawler.
            self.status = 200
            self.html = html.fromstring('<html></html>')
