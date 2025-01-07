from juriscraper.opinions.united_states.state import idaho_civil


class Site(idaho_civil.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.isc.idaho.gov/appeals-court/coa_civil"
        self.court_id = self.__module__

    def get_class_name(self):
        return "idahoctapp_civil"

    def get_court_name(self):
        return "Idaho Court of Appeals"
