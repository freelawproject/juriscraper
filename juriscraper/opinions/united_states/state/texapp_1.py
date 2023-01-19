# Scraper for Texas 1st Court of Appeals
# CourtID: texapp1
# Court Short Name: TX
# Author: Andrei Chelaru
# Reviewer:
# Date: 2014-07-10


from juriscraper.opinions.united_states.state import tex


class Site(tex.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "capp_1"
        self.checkbox = 2
