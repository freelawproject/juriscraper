# Scraper for Florida 4th District Court of Appeal Per Curiam Opinions
# CourtID: flaapp4pc
# Court Short Name: flaapp4pc

from juriscraper.opinions.united_states.state import fladistctapp_4_written


class Site(fladistctapp_4_written.Site):
    """Web Interface: http://www.4dca.org/opinions_auto/most_recent_pc.shtml"""

    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.set_url("p")
