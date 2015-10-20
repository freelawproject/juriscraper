#  Scraper for Iowa Appeals Court
# CourtID: iowactapp
# Court Short Name: iowactapp
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 25 July 2014


from datetime import date

from juriscraper.opinions.united_states.state import iowa


class Site(iowa.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = date.today().year
        self.url = 'http://www.iowacourts.gov/About_the_Courts/Court_of_Appeals/Court_of_Appeals_Opinions/Opinions_Archive/'
