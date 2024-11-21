from datetime import datetime

from juriscraper.opinions.united_states.state import nm


class Site(nm.Site):
    court_code = "183"
    first_opinion_date = datetime(1967, 3, 26)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

    def get_class_name(self):
        return "nmctapp"

    def get_court_name(self):
        return "New Mexico Court of Appeals"
