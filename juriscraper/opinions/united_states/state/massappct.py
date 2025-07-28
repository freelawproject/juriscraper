"""
Scraper for Massachusetts Appeals Court
CourtID: massapp
Court Short Name: MS
Author: Andrei Chelaru
Court Contact: SJCReporter@sjc.state.ma.us (617) 557-1030
Reviewer: mlr
Date: 2014-07-12
History:
    - Update 2023-01-28 by William E. Palin
"""

from datetime import datetime

from juriscraper.opinions.united_states.state import mass


class Site(mass.Site):
    court_name = "Appeals Court"
    first_opinion_date = datetime(2017, 6, 15)
