# Scraper for Texas 5th Court of Appeals
# CourtID: txctapp5
# Court Short Name: TX
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-10


from juriscraper.opinions.united_states.state import texapp_released


class Site(texapp_released.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_number = "05"
        self.checkbox = 6
        self.url = "https://search.txcourts.gov/DocketSrch.aspx?coa=coa05&s=c"
