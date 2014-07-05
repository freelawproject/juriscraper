# Scraper for Oklahoma Court of Civil Appeals
#CourtID: oklacivapp
#Court Short Name: OK
#Author: Andrei Chelaru
#Reviewer:
#Date: 2014-07-05

from datetime import date
import time
import re

from juriscraper.opinions.united_states.state import okla


class Site(okla.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        d = date.today()
        self.url = 'http://www.oscn.net/applications/oscn/Index.asp?ftdb=STOKCSCV&year={year}&level=1'.format(
            year=d.year
        )