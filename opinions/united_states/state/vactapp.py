from juriscraper.opinions.united_states.state import va


class Site(va.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.courts.state.va.us/scndex.htm'
        self.court_id = self.__module__



