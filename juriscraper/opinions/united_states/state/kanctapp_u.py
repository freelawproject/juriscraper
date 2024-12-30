# Scraper for Kansas Appeals Court (unpublished)
# CourtID: kanctapp_u

from juriscraper.opinions.united_states.state import kan_p


class Site(kan_p.Site):
    court_filter = "Court of Appeals"
    status_filter = "Unpublished"
