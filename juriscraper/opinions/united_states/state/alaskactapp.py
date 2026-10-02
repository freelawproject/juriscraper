"""Scraper for the Alaska Court of Appeals
CourtID: alaskactapp
Court Short Name: Alaska Ct. App.

The Court of Appeals shares the Westlaw "Alaska Case Law Service" search feed
with the Supreme Court; we filter to its court label. See alaska.py and #2009.
"""

from juriscraper.opinions.united_states.state import alaska


class Site(alaska.Site):
    court_label = "Alaska App."
