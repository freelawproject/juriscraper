from juriscraper.opinions.united_states.federal_appellate import ca2_p


class Site(ca2_p.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "http://www.ca2.uscourts.gov/decisions?IW_DATABASE=SUM&IW_FIELD_TEXT=*&IW_SORT=-Date&IW_BATCHSIZE=100"
        self.court_id = self.__module__
