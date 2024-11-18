# Scraper for Kansas Supreme Court (unpublished)
# CourtID: kan_u

from juriscraper.opinions.united_states.state import kan_p


class Site(kan_p.Site):
    court_filter = "Supreme Court"
    status_filter = "Unpublished"
