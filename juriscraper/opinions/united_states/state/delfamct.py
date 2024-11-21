#  Scraper for the Family Court of Delaware
# Author: Deepak Kumar
# Date created: 14 Nov 2024

from juriscraper.opinions.united_states.state import delaware


class Site(delaware.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court="Family Court"
        self.court_id = self.__module__

    def get_class_name(self):
        return "delfamct"

    def get_court_name(self):
        return "Family Court of Delaware"
