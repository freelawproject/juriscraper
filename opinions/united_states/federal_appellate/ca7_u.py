import ca7_p

class Site(ca7_p.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = "http://www.ca7.uscourts.gov/fdocs/docs.fwx?yr=&num=&Submit=Past+Week&dtype=Nonprecedential+Disposition&scrid=Select+a+Case"
        self.court_id = self.__module__
