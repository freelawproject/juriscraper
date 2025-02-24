
from juriscraper.opinions.united_states.federal_district import gov_info


class Site(gov_info.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "United States Bankruptcy Court Eastern District of Tennessee"

    def get_class_name(self):
        return "bank_ed_tenn"

    def get_court_type(self):
        return 'Bankruptcy'

    def get_state_name(self):
        return "6th Circuit"

    def get_court_name(self):
        return "Bankruptcy Court Eastern District of Tennessee"