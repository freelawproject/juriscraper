# Scraper for Texas 5th Court of Appeals
# CourtID: texapp5
# Court Short Name: TX
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-10


from juriscraper.opinions.united_states.state import tex


class Site(tex.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "capp_5"
        self.checkbox = 6
    def get_court_name(self):
        return "Texas Court of Appeals"

    def get_class_name(self):
        return "texapp_5"
