from datetime import datetime

from juriscraper.opinions.united_states.state import nj


class Site(nj.Site):
    # there is 1 opinion for datetime(2011, 5, 3),
    # but then none until Feb 2017
    first_opinion_date = datetime(2011, 5, 3)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = self.url = (
            "https://www.njcourts.gov/attorneys/opinions/unpublished-tax"
        )
        self.status = "Unpublished"
