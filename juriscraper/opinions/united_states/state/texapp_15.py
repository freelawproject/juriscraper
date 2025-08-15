# Scraper for Texas 15th Court of Appeals
# CourtID: texapp15
# Court Short Name: TX
# Author: Luis Manzur
# Reviewer: grossir
# Date: 2014-07-10


from juriscraper.opinions.united_states.state import texapp


class Site(texapp.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "capp_15"
        self.checkbox = 16
