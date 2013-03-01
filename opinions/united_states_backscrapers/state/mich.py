from juriscraper.opinions.united_states.state import mich

class Site(mich.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__

    def _download_backwards(self, page):
        if page <= 21711:
            self.url = "http://courts.mi.gov/opinions_orders/opinions_orders/Pages/default.aspx?SearchType=4&Status_Advanced=sct&FirstDate_Advanced=7%2f1%2f1996&LastDate_Advanced=3%2f1%2f2013&PageIndex=" + str(page)

        self.html = self._download()
