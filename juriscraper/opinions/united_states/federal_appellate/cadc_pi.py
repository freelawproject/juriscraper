"""Scraper for Public Interest Cases for the CADC
CourtID: cadc
Court Short Name: Court of Appeals of the District of Columbia
Author: flooie
History:
  2021-12-18: Created by flooie
  2023-01-12: Fixed requests.exceptions.InvalidURL error, by grossir
  2024-12-31: Implemented new site, by grossir
"""

from juriscraper.opinions.united_states.federal_appellate import cadc


class Site(cadc.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # https://media.cadc.uscourts.gov/orders/
        self.url = "https://media.cadc.uscourts.gov/orders/bydate/recent"
