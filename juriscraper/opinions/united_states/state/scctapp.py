"""Scraper for South Carolina Supreme Court
CourtID: scctapp
Court Short Name: S.C. Ct. App.
Author: Varun Iyer
History:
 - 07-23-2018: Created.
"""

from juriscraper.opinions.united_states.state import sc


class Site(sc.Site):
    court = "court-of-appeals"
