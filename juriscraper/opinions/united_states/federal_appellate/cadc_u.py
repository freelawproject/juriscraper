from juriscraper.opinions.united_states.federal_appellate import cadc


class Site(cadc.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # https://media.cadc.uscourts.gov/judgments/
        self.url = "https://media.cadc.uscourts.gov/judgments/bydate/recent"
        self.status = "Unpublished"
