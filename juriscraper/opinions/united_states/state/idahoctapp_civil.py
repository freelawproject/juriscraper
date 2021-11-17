from juriscraper.opinions.united_states.state import idaho_civil


class Site(idaho_civil.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.isc.idaho.gov/appeals-court/coa_civil"
        self.court_id = self.__module__
