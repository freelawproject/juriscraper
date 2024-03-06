# Scraper for Texas 1st Court of Appeals
# CourtID: texapp1
# Court Short Name: TX
# Author: Andrei Chelaru
# Reviewer:
# Date: 2014-07-10


from juriscraper.opinions.united_states.state import tex


class Site(tex.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = "capp_1"
        self.checkbox = 2

    def get_opinions(self, html):
        """
        Cluster with 2 opinions (Court of Appeals)
        https://search.txcourts.gov/Case.aspx?cn=02-22-00347-CV&coa=coa02
        Counter Examples:

        'opinion' in text, but it is actually a letter
        https://search.txcourts.gov/Case.aspx?cn=01-23-00777-CR&coa=coa01
        """
        raise NotImplementedError("...")
