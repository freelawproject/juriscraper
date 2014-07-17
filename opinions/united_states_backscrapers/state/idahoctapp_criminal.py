import idahoctapp_civil


class Site(idahoctapp_civil.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.isc.idaho.gov/opinions/cacrim.htm'
        self.court_id = self.__module__
