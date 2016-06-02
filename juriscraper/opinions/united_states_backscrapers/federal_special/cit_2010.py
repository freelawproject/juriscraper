from juriscraper.opinions.united_states.federal_special import cit

import time
from datetime import date
from lxml import html


class Site(cit.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
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

    def _get_download_urls(self):
        return [t for t in self.html.xpath('//table[3]//tr/td[1]/a/@href')]

    def _get_neutral_citations(self):
        return [t for t in self.html.xpath('//table[3]//tr/td[1]/a/text()')]

    def _get_case_names(self):
        # Exclude confidential rows
        case_names = []
        for e in self.html.xpath('//table[3]/tr[position() > 1]/td[2]'):
            s = html.tostring(e, method='text', encoding='unicode')
            if "confidential" in s:
                continue
            elif 'Errata' in s:
                index = s.find('Errata')
            elif 'Public version' in s:
                index = s.find('Public version')
            else:
                index = -1
            case_names.append(s[:index] if index > -1 else s)
        return case_names

    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath('//table[3]//tr[position() > 1]/td[2][../td/a]'):
            s = html.tostring(e, method='text', encoding='unicode').lower().strip()
            if "errata" in s:
                statuses.append('Errata')
            else:
                statuses.append('Published')
        return statuses

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//table[3]//tr[position() > 1]/td[4][../td/a]'):
            docket_numbers.append(html.tostring(
                                e, method='text', encoding='unicode').strip())
        return docket_numbers

    def _get_judges(self):
        judges = []
        for e in self.html.xpath('//table[3]//tr[position() > 1]/td[5][../td/a]'):
            s = html.tostring (e, method='text', encoding='unicode')
            judges.append(s)
        return judges

    def _get_nature_of_suit(self):
        return [t for t in self.html.xpath('//table[3]//tr/td[6][../td/a]/text()')]

