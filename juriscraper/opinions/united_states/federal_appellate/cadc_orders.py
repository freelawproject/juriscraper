from juriscraper.opinions.united_states.federal_appellate import cadc


class Site(cadc.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_type='orders'

    def get_class_name(self):
        return "cadc_orders"
