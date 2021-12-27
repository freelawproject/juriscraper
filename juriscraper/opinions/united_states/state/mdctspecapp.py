"""
Scraper for Maryland Court of Special Appeals
CourtID: mdctspecapp
Court Short Name: MD
Author: Andrei Chelaru
Date created: 06/27/2014
"""


from datetime import date

from juriscraper.opinions.united_states.state import md


class Site(md.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.mdcourts.gov/cgi-bin/indexlist.pl?court=cosa&year={current_year}&order=bydate&submit=Submit".format(
            current_year=date.today().year
        )
        self.court_id = self.__module__
