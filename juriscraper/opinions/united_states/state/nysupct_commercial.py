"""Scraper and Back Scraper for New York Commercial Division
CourtID: nysupct_commercial
Court Short Name: NY
History:
 - 2024-01-05, grossir: modified to use nytrial template
"""

from datetime import date

from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    base_url = "https://nycourts.gov/reporter/slipidx/com_div_idxtable.shtml"
    court_regex = r".*"
    first_opinion_date = date(2013, 7, 1)
