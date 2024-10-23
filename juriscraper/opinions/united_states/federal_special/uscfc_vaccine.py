"""Scraper for the United States Court of Federal Claims
CourtID: uscfc
Court Short Name: Fed. Cl."""

from juriscraper.opinions.united_states.federal_special import uscfc


class Site(uscfc.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://ecf.cofc.uscourts.gov/cgi-bin/CFC_RecentDecisionsOfTheSpecialMasters.pl"
