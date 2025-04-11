from juriscraper.opinions.united_states.state import ga


class Site(ga.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court="interlocutory"

    def get_class_name(self):
        return "ga_interlocutory"