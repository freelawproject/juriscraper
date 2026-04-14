"""
Scraper for Kansas Court of Appeals - Unpublished
CourtID: kanctapp_u
Court Short Name: Kansas Ct. App.
History:
 - 2026-04-02: Created by splitting kanctapp into kanctapp_p and kanctapp_u. grossir
"""

from juriscraper.opinions.united_states.state import kanctapp_p


class Site(kanctapp_p.Site):
    status_filter = "0"
    status = "Unpublished"
