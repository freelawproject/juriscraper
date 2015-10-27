"""
Scraper for the United States Bankruptcy Appellate Panel for the Tenth Circuit
CourtID: bap10
Court Short Name: 10th Cir. BAP
Auth: Jon Andersen <janderse@gmail.com>
Reviewer: mlr
History:
    2014-09-01: First draft by Jon Andersen
    2014-09-02: Revised by mlr to use _clean_text() instead of pushing logic
                into the _get_case_dates function.
"""

from datetime import datetime
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.bap10.uscourts.gov/opinions/new/opinion.txt'
        self.court_id = self.__module__
        self.my_case_names = []
        self.my_download_urls = []
        self.my_docket_numbers = []

    def _clean_text(self, text):
        """This page is a txt file, so here we convert it to something that
        can be easily ingested by lxml.

        Lines like:
          13-94.pdf|13|94|08/25/2014|Steve Christensen|Raymond Madsen|United States Bankruptcy Court for the District of Utah
        """
        # Nuke duplicates
        lines = set([line for line in text.split('\n') if line])

        # Build an XML tree.
        xml_text = '<rows>\n'
        for line in lines:
            values = line.split('|')
            xml_text += '  <row>\n'
            for value in values:
                xml_text += '    <value>%s</value>\n' % value
            xml_text += '  </row>\n'
        xml_text += '</rows>\n'
        return xml_text

    def _get_case_dates(self):
        path = '//row/value[4]/text()'
        return [datetime.strptime(date_string, '%m/%d/%Y').date()
                for date_string in self.html.xpath(path)]

    def _get_case_names(self):
        plaintiffs = self.html.xpath('//row/value[6]/text()')
        defendants = self.html.xpath('//row/value[7]/text()')
        case_names = []
        for p, d in zip(plaintiffs, defendants):
            case_names.append("%s v. %s" % (p, d))
        return case_names

    def _get_download_urls(self):
        years = self.html.xpath('//row/value[2]/text()')
        file_names = self.html.xpath('//row/value[1]/text()')
        urls = []
        for y, f_n in zip(years, file_names):
            urls.append('http://www.bap10.uscourts.gov/opinions/%s/%s' % (y, f_n))
        return urls

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_dates)

    def _get_docket_numbers(self):
        years = self.html.xpath('//row/value[2]/text()')
        numbers = self.html.xpath('//row/value[3]/text()')
        docket_numbers = []
        for y, n in zip(years, numbers):
            docket_numbers.append("%s-%s" % (y, n))
        return docket_numbers
