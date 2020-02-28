from juriscraper.opinions.united_states_backscrapers.state import (
    idahoctapp_civil,
)


class Site(idahoctapp_civil.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "http://www.isc.idaho.gov/opinions/cacrim.htm"
        self.court_id = self.__module__
