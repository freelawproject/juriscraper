# Scraper for Florida 3rd District Court of Appeal Per Curiam
# CourtID: flaapp3
# Court Short Name: flaapp3

from juriscraper.opinions.united_states.state import fladistctapp_1


class Site(fladistctapp_1.Site):
    number = "third"
    court_index = "3"
