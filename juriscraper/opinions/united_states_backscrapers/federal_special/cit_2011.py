from juriscraper.opinions.united_states.federal_special import cit


class Site(cit.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "http://www.cit.uscourts.gov/SlipOpinions/SlipOps-2011.html"
        self.court_id = self.__module__
