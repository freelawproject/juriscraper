from juriscraper.opinions.united_states_backscrapers.federal_special import cit_2010

import time
from datetime import date
from lxml import html


class Site(cit_2010.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.cit.uscourts.gov/SlipOpinions/SlipOps-2009.html'
        self.court_id = self.__module__

    def _get_case_dates(self):
        case_dates = []
        for e in self.html.xpath('//table[3]/tr/td[3][../td/a]'):
            date_string = html.tostring(e, method='text', encoding='unicode').strip()
            if date_string == "05/13/20009":
                # Special case.
                date_string = "05/13/2009"
            case_dates.append(date.fromtimestamp(
                         time.mktime(time.strptime(date_string, '%m/%d/%Y'))))
        return case_dates

    def _get_nature_of_suit(self):
        return None
