import idaho_civil


class Site(idaho_civil.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.isc.idaho.gov/opinions/sccrim.htm'
        self.court_id = self.__module__
