"""Scraper for Mississippi Court of Appeals
CourtID: missctapp
Court Short Name: Miss. Ct. App.
Author: Jon Andersen
History:
    2014-06-21: Created by Jon Andersen
    2021-12-16: Update by satsuki-chan
"""

from juriscraper.opinions.united_states.state import miss


# Landing page: https://courts.ms.gov/appellatecourts/coa/coadecisions.php
class Site(miss.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court = "COA"
