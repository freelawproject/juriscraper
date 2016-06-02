# Author: Michael Lissner
# Date created: 2013-06-03

import re
import time
from datetime import date
from datetime import timedelta

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        thirty_days_ago = date.today() - timedelta(days=30)
        # Oddly, all the empty get params are needed. This site uses the Spring Framework, as gleaned in a stacktrace.
        self.url = ('http://searchcourts.mt.gov/search/advanced?searchtype=advanced&txtContainsOne=&cboAndOrOne='
                    '&txtContainsTwo=&cboAndOrTwo=&txtContainsThree=&cboDocumentType=Opinion%%2FOrder'
                    '&txtCaseNumber=&txtCitation=&txtPartyNameOne=&txtPartyNameTwo=&cboCaseType=&cboOpinionBy='
                    '&txtAttorneyNameOne=&txtAttorneyNameTwo=&txtTrialCourtJudge=&txtTrialCourtCaseNumber='
                    '&cboFromYear=%s'
                    '&cboFromMonth=%s'
                    '&cboFromDay=%s'
                    '&cboToYear=%s'
                    '&cboToMonth=%s'
                    '&cboToDay=%s' % (thirty_days_ago.year, thirty_days_ago.month, thirty_days_ago.day,
                                      today.year, today.month, today.day))
        self.back_scrape_iterable = range(1972, 2014)

    def _get_download_urls(self):
        path = '//table[@id="anyid"]/tr[position() > 1]/td[1]/a/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//table[@id="anyid"]/tr[position() > 1]/td[2]/text()'
        return [titlecase(case_name) for case_name in self.html.xpath(path)]

    def _get_case_dates(self):
        path = '//table[@id="anyid"]/tr[position() > 1]/td[8]/text()'
        return [date.fromtimestamp(time.mktime(time.strptime(date_string, '%Y/%m/%d')))
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        for s in self.html.xpath('//table[@id="anyid"]/tr[position() > 1]/td[3]/text()'):
            if re.search('[A-Za-z]', s):
                try:
                    docket_numbers.append(s.split()[1])
                except IndexError:
                    docket_numbers.append(s)
            else:
                docket_numbers.append(s)
        return docket_numbers

    def _get_nature_of_suit(self):
        path = '//table[@id="anyid"]/tr[position() > 1]/td[3]/text()'
        natures = []
        for s in self.html.xpath(path):
            if 'DA' in s:
                nature = "Direct Appeal"
            elif 'OP' in s:
                nature = "Original Proceeding"
            elif 'PR' in s:
                nature = 'Professional Regulation'
            elif 'AF' in s:
                nature = 'Administrative File'
            else:
                nature = 'Unknown'
            natures.append(nature)
        return natures

    def _get_neutral_citations(self):
        path = '//table[@id="anyid"]/tr[position() > 1]/td[5]/text()'
        return list(self.html.xpath(path))

    def _download_backwards(self, year):
        self.url = ('http://searchcourts.mt.gov/search/advanced?searchtype=advanced&txtContainsOne=&cboAndOrOne='
                    '&txtContainsTwo=&cboAndOrTwo=&txtContainsThree=&cboDocumentType=Opinion%%2FOrder'
                    '&txtCaseNumber=&txtCitation=&txtPartyNameOne=&txtPartyNameTwo=&cboCaseType=&cboOpinionBy='
                    '&txtAttorneyNameOne=&txtAttorneyNameTwo=&txtTrialCourtJudge=&txtTrialCourtCaseNumber='
                    '&cboFromYear=%s'
                    '&cboFromMonth=%s'
                    '&cboFromDay=%s'
                    '&cboToYear=%s'
                    '&cboToMonth=%s'
                    '&cboToDay=%s' % (year, '01', '01',
                                      year, '12', '31'))
        self.html = self._download()
