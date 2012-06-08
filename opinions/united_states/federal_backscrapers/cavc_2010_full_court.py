# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
import cavc

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/2010FullCourtOrders.cfm'
        self.court_id = self.__module__