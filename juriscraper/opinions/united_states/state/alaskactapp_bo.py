from juriscraper.opinions.united_states.state import alaska, alaskactapp


class Site(alaskactapp.Site):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://appellate-records.courts.alaska.gov/CMSPublic/Home/BailOrders"
        self.opinion_type="bail orders"

    def get_class_name(self):
        return "alaskactapp_bo"
