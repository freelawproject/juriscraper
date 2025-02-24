from juriscraper.opinions.united_states.state import mo


class Site(mo.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court = "Western"
        # self.url = self.build_url()

    def get_class_name(self):
        return "moctapp_western"

    def get_court_name(self):
        return "Missouri Court of Appeals"
