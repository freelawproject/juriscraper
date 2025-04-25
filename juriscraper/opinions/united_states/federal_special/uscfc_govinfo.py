from juriscraper.opinions.united_states.federal_district import gov_info


class Site(gov_info.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "United States Court of Federal Claims"

    def get_class_name(self):
        return "uscfc_govinfo"

    def get_court_type(self):
        return 'Special'

    def get_state_name(self):
        return "Claims"

    def get_court_name(self):
        return "US Court of Federal Claims"