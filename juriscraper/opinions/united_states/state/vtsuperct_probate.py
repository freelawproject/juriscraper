"""Scraper for the Vermont Superior Court, Probate Division
CourtID: vtsuperct
Court Short Name: Vermont Superior Court
Court Contact: submit form here https://www.vtcourts.gov/website-feedback-form
"""

from juriscraper.opinions.united_states.state import vtsuperct_civil


class Site(vtsuperct_civil.Site):
    division = 6
    days_interval = 200
