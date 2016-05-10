# Scraper for New York Appellate Divisions 2nd Dept.
#CourtID: nyappdiv_2nd
#Court Short Name: NY
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-04

from juriscraper.opinions.united_states.state import nyappdiv_1st


class Site(nyappdiv_1st.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        # This is the URL for the past months
        # d = date.today()
        # self.url = 'http://www.courts.state.ny.us/reporter/slipidx/aidxtable_2_{year}_{month}.shtml'.format(
        #     year=d.year,
        #     mon=d.strftime("%B"))

        # This is the URL for the current month
        self.url = 'http://www.courts.state.ny.us/reporter/slipidx/aidxtable_2.shtml'
        self.court_id = self.__module__
