# Scraper for the United States Court of International Trade
# CourtID: cit
# Court Short Name: Ct. Int'l Trade
# Neutral Citation Format: Ct. Int'l Trade No. 12-1
from juriscraper.GenericSite import GenericSite
import re
import time
from datetime import date
from lxml import html

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.cit.uscourts.gov/SlipOpinions/index.html'
# Backscraping 2011 is possible with this scraper using the following url:
#        self.url = 'http://www.cit.uscourts.gov/SlipOpinions/SlipOps-2011.html'
# To scrape earlier years, see separate scrapers of form: cit_2010.py
        self.court_id = self.__module__

# Unlike all the other metadata, we do not need to check to see if these
# include a confidential row, because those rows don't have urls at all.
    def _get_download_urls(self):
        return [t for t in self.html.xpath('//table[4]/tr/td[1]/a/@href')]

# We add a check to make sure we don't include a 'confidential' row.
# This is done in xpath by looking for siblings with an a.
    def _get_neutral_citations(self):
        return [t for t in self.html.xpath('//table[4]/tr/td[1]/a/text()')]
    
    def _get_case_names(self):
# Skip rows containing confidential cases, because there is no associated doc.
# We also strip "Errata: mm/dd/yyyy" from the case names of errata docs.
        case_names = []
        for e in self.html.xpath('//table[4]/tr[position() > 1]/td[2]'):
            s = html.tostring(e, method='text', encoding='unicode')
            if "confidential" in s:
                continue
            else:
                if "Errata" in s:
                    case_names.append(s.strip()[:-18])
                else:
                    case_names.append(s)
        return case_names

# We add a check to make sure we don't include a 'confidential' row.
# This is done in xpath by looking for siblings with an a.
    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath('//table[4]/tr[position() > 1]/td[2][../td/a]'):        
            s = html.tostring(e, method='text', encoding='unicode').lower().strip()
            if "errata" in s:
                statuses.append('Errata')
            else:
                statuses.append('Published')
        return statuses

# This does not capture the release dates for the errata documents.
# The errata release date is listed in column 2. This will use the original
# release date instead.
# We add a check to make sure we don't include a 'confidential' row.
# This is done in xpath by looking for siblings with an a.
    def _get_case_dates(self):
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y')))
            for date_string in self.html.xpath('//table[4]/tr/td[3][../td/a]/text()')]

# We add a check to make sure we don't include a 'confidential' row.
# This is done in xpath by looking for siblings with an a.
# Because there can be multiple docket numbers we have to replace some newlines.
    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//table[4]/tr[position() > 1]/td[4][../td/a]'):
            s = html.tostring (e, method='text', encoding='unicode').strip()
            docket_numbers.append(s.replace('\r\n', ' &'))
        return docket_numbers

# We add a check to make sure we don't include a 'confidential' row.
# This is done in xpath by looking for siblings with an a.
# Because there are sometimes multiple judges we have to strip some whitespace.
    def _get_judges(self):
        judges = []
        for e in self.html.xpath('//table[4]/tr[position() > 1]/td[5][../td/a]'):
            s = html.tostring (e, method='text', encoding='unicode')
            judges.append(s.strip())
        return judges

# We add a check to make sure we don't include a 'confidential' row.
# This is done in xpath by looking for siblings with an a.
    def _get_nature_of_suit(self):
        return [t for t in self.html.xpath('//table[4]/tr/td[6][../td/a]/text()')]
