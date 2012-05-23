import cit


class Site(cit.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.cit.uscourts.gov/SlipOpinions/SlipOps-2011.html'
        self.court_id = self.__module__

