"""
Scraper for Kansas Court of Appeals
CourtID: kanctapp
Court Short Name: Kansas Ct. App.
Author: William Palin
Court Contact:
History:
 - 2023-01-04: Created.
 - 2026-03-19: Refactored from WebDriven to OpinionSiteLinear. Added backscraper. grossir
"""

from juriscraper.opinions.united_states.state import kan


class Site(kan.Site):
    court_string = "Court of Appeals"
    court_filter = "20"
    days_interval = 15
