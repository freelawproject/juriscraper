from juriscraper.opinions.united_states.federal_appellate import (
    scotus_chambers,
)


class Site(scotus_chambers.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.precedential = "Relating-to"
        self.court = "relatingtoorders"
