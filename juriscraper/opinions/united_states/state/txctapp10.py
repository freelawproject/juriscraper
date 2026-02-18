# Scraper for Texas 10th Court of Appeals
# CourtID: txctapp10
# Court Short Name: TX
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-10


from juriscraper.opinions.united_states.state import texapp


class Site(texapp.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "capp_10"
        self.court_number = "10"
        self.checkbox = 11
