# Scraper for New York Appellate Divisions 2nd Dept.
# CourtID: nyappdiv_2nd
# Court Short Name: NY
# Author: Andrei Chelaru
# Reviewer: mlr
# Date: 2014-07-04
from datetime import date

from juriscraper.opinions.united_states.state import nyappdiv_1st


class Site(nyappdiv_1st.Site):
    first_opinion_date = date(2003, 9, 25)
    days_interval = 30
    court = "App Div, 2d Dept"
