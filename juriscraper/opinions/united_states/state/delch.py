#  Scraper for the Court Of Chancery of Delaware
# CourtID: dechan
# Court Short Name: De.
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 31 July 2014

from juriscraper.opinions.united_states.state import delaware


class Site(delaware.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://courts.delaware.gov/opinions/List.aspx?ag=Court%20of%20Chancery'
        self.court_id = self.__module__
