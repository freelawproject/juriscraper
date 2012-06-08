import ca3_p

class Site(ca3_p.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = "http://www.ca3.uscourts.gov/recentop/week/recnonprec.htm"
        self.court_id = self.__module__
