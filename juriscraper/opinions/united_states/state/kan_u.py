"""
CourtID: kan_u
Court Short Name: Kansas Supreme Court (Unpublished)
History:
    2025-06-05, quevon24: Implemented new site
"""

from juriscraper.opinions.united_states.state import kan_p


class Site(kan_p.Site):
    court_filter = 10  # Supreme Court
    status_filter = 0  # Unpublished
