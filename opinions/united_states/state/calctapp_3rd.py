# Scraper for California's Third District Court of Appeal 
# CourtID: calctapp_3rd
# Court Short Name: Cal. Ct. App.
from juriscraper.opinions.united_states.state import cal
import re
import time
from datetime import date


class Site(cal.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.courtinfo.ca.gov/cgi-bin/opinions-blank.cgi?Courts=C'
        self.court_id = self.__module__

    def _get_division(self):
        return ['3rd App. Dist.'] * len(self.case_names)
