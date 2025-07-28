"""
Scraper for Kansas Court of Appeals
CourtID: kanctapp
Court Short Name: Kansas Ct. App.
Author: William Palin
Court Contact:
History:
 - 2023-01-04: Created.
Notes:
 - selenium
"""

from juriscraper.opinions.united_states.state import kan


class Site(kan.Site):
    link_xp = '//div[@class="col-md-6"][2]/ul/li'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
