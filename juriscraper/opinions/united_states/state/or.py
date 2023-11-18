"""
History:
 - 2014-08-05: Adapted scraper to have year-based URLs.
 - 2023-11-18: Fixed and updated
"""

from juriscraper.opinions.united_states.state import orctapp


class Site(orctapp.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://www.courts.oregon.gov/publications/sc/Pages/default.aspx"
        )
        self.status = "Published"
        self.court_code = "p17027coll3"
