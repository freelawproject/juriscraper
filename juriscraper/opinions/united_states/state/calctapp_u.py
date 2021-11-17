from juriscraper.opinions.united_states.state import cal


class Site(cal.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.courts.ca.gov/cms/npopinions.htm"
        self.court_id = self.__module__

    def build_url(self):
        return "https://www.courts.ca.gov/cms/npopinions.htm"

    def _get_precedential_statuses(self):
        return ["Unpublished"] * len(self.case_names)
