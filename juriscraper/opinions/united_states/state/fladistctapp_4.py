# Scraper for Florida 4th District Court of Appeal Per Curiam
# CourtID: flaapp4
# Court Short Name: flaapp4

from juriscraper.opinions.united_states.state import fladistctapp_1


class Site(fladistctapp_1.Site):
    number = "fourth"
    court_index = "4"
