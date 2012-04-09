import ca11_p

class Site(ca11_p.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.ca11.uscourts.gov/unpub/searchdate.php'
        self.court_id = self.__module__
