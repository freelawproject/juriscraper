"""Scraper for the Vermont Environmental
CourtID: vt
Court Short Name: VT
Court Contact: submit form here https://www.vermontjudiciary.org/website-feedback-form
"""

from juriscraper.opinions.united_states.state import vt
from juriscraper.OpinionSite import OpinionSite


class Site(vt.Site):
    division = 1
    days_interval = 100
    # Deactivate extract_from_text from parent class
    # and avoid triggering the example requirement from
    # tests.local.test_ScraperExtractFromTextTest
    # Other vtsuperct_* scrapers will inherit from this one
    # to inherit the same behaviour
    extract_from_text = OpinionSite.extract_from_text
