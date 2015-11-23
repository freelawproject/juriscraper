# Scraper for Texas 3rd Court of Appeals
#CourtID: texapp3
#Court Short Name: TX
#Author: Andrei Chelaru
#Reviewer: mlr
#Date: 2014-07-10


from juriscraper.opinions.united_states.state import tex


class Site(tex.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = 'capp_3'
