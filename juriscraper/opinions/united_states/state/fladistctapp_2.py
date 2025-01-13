# Scraper for Florida 2nd District Court of Appeal Per Curiam
# CourtID: flaapp2
# Court Short Name: flaapp2

from juriscraper.opinions.united_states.state import fladistctapp_1


class Site(fladistctapp_1.Site):
    number = "second"
    court_index = "2"
