import cit

import time
from datetime import date
from lxml import html


class Site(cit.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.cit.uscourts.gov/SlipOpinions/SlipOps-2010.html'
        self.court_id = self.__module__

    def _get_case_dates(self):
        case_dates = []
        for e in self.html.xpath('//table[3]/tr/td[3][../td/a]'):
            date_string = html.tostring(e, method='text', encoding='unicode').strip()
            if date_string == "06/25//2010":
                # Special case.
                date_string = "06/25/2010"
            case_dates.append(date.fromtimestamp(
                         time.mktime(time.strptime(date_string, '%m/%d/%Y'))))
        return case_dates
