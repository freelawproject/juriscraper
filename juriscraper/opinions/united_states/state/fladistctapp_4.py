# Scraper for Florida 4th District Court of Appeal Per Curiam
# CourtID: flaapp4
# Court Short Name: flaapp4

from juriscraper.opinions.united_states.state import fladistctapp_1


class Site(fladistctapp_1.Site):
    scopes = "fourth_district_court_of_appeal"
    site_access = "4dca"
