from datetime import datetime

from juriscraper.opinions.united_states.state import nj


class Site(nj.Site):
    first_opinion_date = datetime(2017, 5, 25)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = self.url = (
            "https://www.njcourts.gov/attorneys/opinions/published-tax"
        )
        self.status = "Published"
