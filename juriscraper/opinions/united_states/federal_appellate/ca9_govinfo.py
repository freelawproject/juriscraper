from juriscraper.opinions.united_states.federal_district import gov_info


class Site(gov_info.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "United States Court of Appeals for the Ninth Circuit"

    def get_class_name(self):
        return "ca9_govinfo"

    def get_court_type(self):
        return 'Federal'

    def get_state_name(self):
        return "9th Circuit"

    def get_court_name(self):
        return "Court of Appeal for the Ninth Circuit"