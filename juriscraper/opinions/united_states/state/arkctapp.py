# Author: Michael Lissner
# Date created: 2013-08-10

from juriscraper.opinions.united_states.state import ark

## WARNING: THIS SCRAPER IS FAILING:
## This scraper is succeeding in development, but
## is failing in production.  We are not exactly
## sure why, and suspect that the hosting court
## site may be blocking our production IP and/or
## throttling/manipulating requests from production.


class Site(ark.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url_id = "courtofappeals"
        self.url = self.get_url()
