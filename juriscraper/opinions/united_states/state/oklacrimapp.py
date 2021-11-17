# Scraper for Oklahoma Court of Criminal Appeals
# CourtID: oklacrimapp
# Court Short Name: OK
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-05

from datetime import date

from juriscraper.opinions.united_states.state import okla


class Site(okla.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        d = date.today()
        self.url = "http://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKCSCR&year={year}&level=1".format(
            year=d.year
        )
