from juriscraper.opinions.united_states.state import va


class Site(va.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.courts.state.va.us/wpcap.htm'
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)



