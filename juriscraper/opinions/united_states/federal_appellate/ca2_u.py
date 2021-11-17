"""Scraper for Second Circuit
CourtID: ca2
Contact:
  Webmaster@ca2.uscourts.gov ('Calendar Team' handles updates, and is responsive)
  ecfhelpdesk@ca2.uscourts.gov
  Shane_Clouden@ca2.uscourts.gov
"""


from juriscraper.opinions.united_states.federal_appellate import ca2_p


class Site(ca2_p.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.ca2.uscourts.gov/decisions?IW_DATABASE=SUM&IW_FIELD_TEXT=*&IW_SORT=-Date&IW_BATCHSIZE=100"
        self.court_id = self.__module__
