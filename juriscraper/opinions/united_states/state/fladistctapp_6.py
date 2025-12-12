# Scraper for Florida 6th District Court of Appeal
# CourtID: flaapp6
# Court Short Name: flaapp6

from juriscraper.opinions.united_states.state import fladistctapp_1


class Site(fladistctapp_1.Site):
    scopes = "sixth_district_court_of_appeal"
    site_access = "6dca"
