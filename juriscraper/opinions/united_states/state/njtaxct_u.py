from datetime import datetime

from juriscraper.opinions.united_states.state import njtaxct_p


class Site(njtaxct_p.Site):
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

    def get_class_name(self):
        return "njtaxct_u"

    def get_court_name(self):
        return "New Jersey Tax Court"
