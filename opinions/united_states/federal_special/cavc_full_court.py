# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
import cavc

# The court has separate pages listing en banc opinions (by year).
class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/EnBancOrders.cfm'
        self.court_id = self.__module__