# Scraper for the United States Court of Appeals for Veterans Claims
# CourtID: cavc
# Court Short Name: Vet.App.
from juriscraper.opinions.united_states.federal_special import cavc

class Site(cavc.Site):
    def __init__(self):
        super(Site, self).__init__()
        # Backscraper for 1st Quarter of 2009.
        self.url = 'http://www.uscourts.cavc.gov/orders_and_opinions/OrdersOpinions2009.html'
        self.court_id = self.__module__