"""
Scraper for Kansas Supreme Court - Unpublished
CourtID: kan_u
Court Short Name: Kansas
History:
 - 2026-04-02: Created by splitting kan into kan_p and kan_u. grossir
"""

from juriscraper.opinions.united_states.state import kan_p


class Site(kan_p.Site):
    status_filter = "0"
    status = "Unpublished"
