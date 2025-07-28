"""Scraper for North Carolina Court of Appeals
CourtID: ncctapp
Court Short Name: N.C. Ct. App.
Author: Jon Andersen
History:
    2014-08-04: Created by Jon Andersen
"""

from juriscraper.opinions.united_states.state import nc


class Site(nc.Site):
    court = "coa"
    court_number = 2
