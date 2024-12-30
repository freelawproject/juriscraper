"""
Scraper for Florida 5th District Court of Appeal
CourtID: flaapp5
Court Short Name: flaapp5
Court Contact: 5dca@flcourts.org, 386-947-1530
Author: Andrei Chelaru
Reviewer: mlr
History:
 - 2014-07-23, Andrei Chelaru: Created.
 - 2014-08-05, mlr: Updated.
 - 2014-08-06, mlr: Updated.
 - 2014-09-18, mlr: Updated date parsing code to handle Sept.
 - 2016-03-16, arderyp: Updated to return proper absolute pdf url paths, simplify date logic
"""

from juriscraper.opinions.united_states.state import fladistctapp_1


class Site(fladistctapp_1.Site):
    number = "fifth"
    court_index = "5"
