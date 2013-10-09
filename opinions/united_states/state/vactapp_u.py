from juriscraper.opinions.united_states.state import va


class Site(va.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.courts.state.va.us/wpcau.htm'
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        return ["Unpublished"] * len(self.case_names)



