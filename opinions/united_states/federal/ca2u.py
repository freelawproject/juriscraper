import ca2p

class Site(ca2p.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = "http://www.ca2.uscourts.gov/decisions?IW_DATABASE=SUM&IW_FIELD_TEXT=*&IW_SORT=-Date&IW_BATCHSIZE=100"
        self.court_id = self.__module__
