"""Scraper for United States District Court for the District of Columbia
CourtID: dcd
Court Short Name: D.D.C.
Author: V. David Zvenyach
Date created: 2014-02-27
Substantially Revised: Brian W. Carver, 2014-03-28
"""

from juriscraper.opinions.united_states_backscrapers.federal_district import dcd_2013

class Site(dcd_2013.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = 'https://ecf.dcd.uscourts.gov/cgi-bin/Opinions.pl?2012'
