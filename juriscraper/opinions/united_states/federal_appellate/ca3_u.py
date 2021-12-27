from juriscraper.opinions.united_states.federal_appellate import ca3_p


class Site(ca3_p.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www2.ca3.uscourts.gov/recentop/week/recnonprec.htm"
        self.court_id = self.__module__
