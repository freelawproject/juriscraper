from juriscraper.opinions.united_states.state import ala


class Site(ala.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://judicial.alabama.gov/decision/criminaldecisions"
