"""
Scraper for Massachusetts Superior Court
CourtID: masssuperct
Court Short Name: MS
Author: Luis Manzur
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Date: 2025-07-16
History:
    - Created by luism
"""

from datetime import datetime

from juriscraper.opinions.united_states.state import mass


class Site(mass.Site):
    court_name = "Superior Court"
    first_opinion_date = datetime(2017, 6, 20)
