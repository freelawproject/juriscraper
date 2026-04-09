# Scraper for New York Appellate Divisions 4th Dept.
# CourtID: nyappdiv_4th
from datetime import date

from juriscraper.opinions.united_states.state import nyappdiv_1st


class Site(nyappdiv_1st.Site):
    first_opinion_date = date(2003, 9, 25)
    days_interval = 30
    court = "App Div, 4th Dept"
