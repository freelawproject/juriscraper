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
# This is a special backscraper to deal with problems on the 2008 page.
        self.url = 'http://www.cit.uscourts.gov/SlipOpinions/SlipOps-2008.html'
        self.court_id = self.__module__

    def _get_download_urls(self):
        download_urls = []
        for e in self.html.xpath('//table[3]/tr[position() > 1]/td[1]'):
            s = html.tostring(e, method='text', encoding='unicode').strip()
            download_urls.append('http://www.cit.uscourts.gov/SlipOpinions/Slip_op08/' + s + '.pdf')
        return download_urls

    def _get_neutral_citations(self):
        neutral_citations = []
        for e in self.html.xpath('//table[3]/tr[position() > 1]/td[1]'):
            s = html.tostring(e, method='text', encoding='unicode').strip()
            neutral_citations.append(s)
        return neutral_citations
        
    def _get_case_names(self):
# We strip "Errata: mm/dd/yyyy" from the case names of errata docs.
        case_names = []
# This gets the first 125 case names
        for t in self.html.xpath('//table[3]/tr[position() > 1]/td[2]/text()'):
            if "Errata" in t:
                case_names.append(t.strip()[:-18])
            else:
                case_names.append(t.strip())
# This gets the other 19 case names
        for e in self.html.xpath('//table[3]/tr[position() > 1]/td[2]/font'):
            s = html.tostring(e, method='text', encoding='unicode')
            if "02/08/08" or "03/04/08" in s:
                case_names.append(s)
            elif "version posted on" in s:
                continue
            elif s == '':
                continue
            else:
                case_names.append(s)
        return case_names
    
    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath('//table[3]/tr[position() > 1]/td[2]'):        
            s = html.tostring(e, method='text', encoding='unicode').lower().strip()
            if "errata" in s:
                statuses.append('Errata')
            else:
                statuses.append('Published')
        return statuses


# This does not capture the release dates for the errata documents.
# The errata release date is listed in column 2. This will use the original
# release date instead.
    def _get_case_dates(self):
        case_dates = []
        for e in self.html.xpath('//table[3]/tr[position() > 1]/td[3]'):
            if html.tostring (e, method='text', encoding='unicode').strip() == "08/05/20008":
                date_string = "08/05/2008"
                case_dates.append(date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y'))))
            else:
                date_string = html.tostring (e, method='text', encoding='unicode').strip()
                case_dates.append(date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y'))))
        return case_dates
"""
# Because there can be multiple docket numbers we have to replace some newlines.
    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//table[3]/tr[position() > 1]/td[4]'):
            s = html.tostring (e, method='text', encoding='unicode').strip()
            docket_numbers.append(s.replace('\r\n', ' &'))
        return docket_numbers

# Comment out the following section if backscraping years 1999-2005.
# Because there are sometimes multiple judges we have to strip some whitespace.
    def _get_judges(self):
        judges = []
        for e in self.html.xpath('//table[3]/tr[position() > 1]/td[5]'):
            s = html.tostring (e, method='text', encoding='unicode')
            judges.append(s.strip())
        return judges
"""