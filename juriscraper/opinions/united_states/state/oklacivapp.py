# Scraper for Oklahoma Court of Civil Appeals
#CourtID: oklacivapp
#Court Short Name: OK
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-05

from datetime import date

from juriscraper.opinions.united_states.state import okla


class Site(okla.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        d = date.today()
        self.url = 'http://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKCSCV&year={year}&level=1'.format(
            year=d.year
        )
