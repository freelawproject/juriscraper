"""
Scraper for Kansas Court of Appeals - Published
CourtID: kanctapp_p
Court Short Name: Kansas Ct. App.
Author: William Palin
Court Contact:
History:
 - 2023-01-04: Created.
 - 2026-03-19: Refactored from WebDriven to OpinionSiteLinear. Added backscraper. grossir
 - 2026-04-02: Split into kanctapp_p and kanctapp_u by status. grossir
"""

from juriscraper.opinions.united_states.state import kan_p


class Site(kan_p.Site):
    court_string = "Court of Appeals"
    court_filter = "20"
    days_interval = 15
