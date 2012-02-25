import scotus_chambers

class Site(scotus_chambers.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.supremecourt.gov/opinions/relatingtoorders.aspx'
        self.court_id = self.__module__
