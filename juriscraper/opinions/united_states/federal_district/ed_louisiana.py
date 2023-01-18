from juriscraper.opinions.united_states.federal_appellate import ca4


class Site(ca4.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.parameters = {
            "offset": 0,
            "sortBy": "2",
            "query": "collection:(USCOURTS) AND courtname:(United States District Court Eastern District of Louisiana)",
            "historical": True,
        }
