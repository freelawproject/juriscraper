"""Scraper and Back Scraper for New York Commercial Division
CourtID: nysupct_commercial
Court Short Name: NY
History:
 - 2024-01-05, grossir: modified to use nytrial template
 - 2026-09-29, renatodvc: use the new "current/index" pages
"""

from datetime import date

from juriscraper.opinions.united_states.state import nytrial


class Site(nytrial.Site):
    base_url = (
        "https://nycourts.gov/reporter/current/index/com_div_idxtable.shtml"
    )
    current_index_start = date(2026, 4, 1)
    court_regex = r".*"
    first_opinion_date = date(2013, 7, 1)
