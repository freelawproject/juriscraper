from juriscraper.OpinionSite import OpinionSite
from juriscraper.opinions.united_states.state import utah


class Site(utah.Site):
    extract_from_text = OpinionSite.extract_from_text

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://legacy.utcourts.gov/opinions/appopin/"
        self.court_id = self.__module__
