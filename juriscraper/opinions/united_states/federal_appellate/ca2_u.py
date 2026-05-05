"""Scraper for Second Circuit Summary Orders
CourtID: ca2
Contact:
  Webmaster@ca2.uscourts.gov ('Calendar Team' handles updates, and is responsive)
  ecfhelpdesk@ca2.uscourts.gov
  Shane_Clouden@ca2.uscourts.gov
"""

from juriscraper.opinions.united_states.federal_appellate import ca2_p


class Site(ca2_p.Site):
    index = "*{aad0964f04f3e9c420e057fd415efe0c} SUM"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Unpublished"
