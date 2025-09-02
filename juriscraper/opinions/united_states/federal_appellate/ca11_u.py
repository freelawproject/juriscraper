from juriscraper.opinions.united_states.federal_appellate import ca11_p


class Site(ca11_p.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://media.ca11.uscourts.gov/opinions/unpub/logname.php"
        self.court_id = self.__module__
        self.back_scrape_iterable = list(range(20, 22000, 20))
        self.should_have_results = True
        self.status = "Unpublished"
