# Scraper for the United States Court of International Trade
# CourtID: cit
# Court Short Name: Ct. Int'l Trade
# Neutral Citation Format: Ct. Int'l Trade No. 12-1
from juriscraper.OpinionSite import OpinionSite
import re
import time
from datetime import date
from lxml import html

class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
# This is a special backscraper to deal with problems on the 2000 page.
        self.url = 'http://www.cit.uscourts.gov/SlipOpinions/SlipOps-2000.html'
        self.court_id = self.__module__

    def _get_download_urls(self):
        return [t for t in self.html.xpath('//table[3]//tr[position() > 1]/td//font//a/@href')]

    def _get_neutral_citations(self):
        neutral_citations = []
        for e in self.html.xpath('//table[3]//tr[position() > 1]/td[1]//font//a'):
            s = html.tostring(e, method='text', encoding='unicode').strip()
            neutral_citations.append(s)
        return neutral_citations

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath('//table[3]//tr[position() > 1]/td[2]/*'):
            s = html.tostring (e, method='text', encoding='unicode').strip()
# We strip "erratum: mm/dd/yyyy" from the case names of errata docs.
            if "errat" in s:
                case_names.append(s.strip()[:-19])
            else:
                case_names.append(s.strip())
        return case_names

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_case_dates(self):
        case_dates = []
        for e in self.html.xpath('//table[3]//tr[position() > 1]/td[3]//font'):
            s = html.tostring (e, method='text', encoding='unicode').strip()
            case_dates.append(date.fromtimestamp(time.mktime(time.strptime(s.strip(), '%m/%d/%Y'))))
        return case_dates

# Because there can be multiple docket numbers we have to replace some newlines.
    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath('//table[3]//tr[position() > 1]/td[4]//font'):
            s = html.tostring (e, method='text', encoding='unicode').strip()
            docket_numbers.append(s.replace('\r\n', ' &'))
        return docket_numbers
