# Scraper for Superior Court of the Virgin Islands (unpublished)
# CourtID: visuper_u

from juriscraper.opinions.united_states.territories import visuper_p


class Site(visuper_p.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://superior.vicourts.org/court_opinions/unpublished_opinions"
        )
        self.status = "Unpublished"
