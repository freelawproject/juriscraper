# Scraper for Texas Criminal Court of Appeals
# CourtID: texcrimapp
# Court Short Name: TX
# Author: Michael Lissner
# Reviewer: None
# Date: 2015-09-02


from juriscraper.opinions.united_states.state import tex


class Site(tex.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.court_name = 'ccrimapp'
