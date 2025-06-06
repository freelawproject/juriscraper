"""
CourtID: kanctapp_u
Court Short Name: Kansas Appeals Court (unpublished)
History:
    2025-06-05, quevon24: Implemented new site
"""

from datetime import datetime

from juriscraper.opinions.united_states.state import kan_p


class Site(kan_p.Site):
    court_filter = 20  # Court of Appeals
    status_filter = 0  # Published
    first_opinion_date = datetime(2015, 8, 1)
