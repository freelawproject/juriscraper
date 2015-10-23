"""
Scraper for New York Court of Appeals
CourtID: ny
Court Short Name: NY
History:
 2014-07-04: Created by Andrei Chelaru, reviewed by mlr.
 2015-10-23: Parts rewritten by mlr.
"""

from lxml import html
from lxml.html import html5parser, fromstring, tostring
import re
from datetime import date, datetime
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.crawl_date = date.today()
        # http://www.nycourts.gov/ctapps/Decisions/2014/Jul14/Jul14.html
        self.url = 'http://www.nycourts.gov/ctapps/Decisions/{year}/{mon}{yr}/{mon}{yr}.html'.format(
            year=self.crawl_date.year,
            yr=self.crawl_date.strftime("%y"),
            mon=self.crawl_date.strftime("%b"))
        self.court_id = self.__module__

    def _make_html_tree(self, text):
        e = html5parser.document_fromstring(text)
        html_tree = fromstring(tostring(e))
        return html_tree

    def _get_case_names(self):
        path = '''//*[count(td)=4 and td[2]//@href[not(contains(., 'DecisionList'))]]'''  # Any element with four td's
        case_names = []
        for element in self.html.xpath(path):
            case_name_parts = []
            for t in element.xpath('./td[4]/p/font/text()'):
                if t.strip():
                    case_name_parts.append(t)
            if not case_name_parts:
                # No hits for first XPath, try another that sometimes works.
                for t in element.xpath('./td[4]//text()'):
                    if t.strip():
                        case_name_parts.append(t)
            if case_name_parts:
                case_names.append(', '.join(case_name_parts))
        return case_names

    def _get_download_urls(self):
        path = '''//*[count(td)=4]/td[2]//@href[not(contains(., 'DecisionList'))]'''
        return self.html.xpath(path)

    def _get_case_dates(self):
        path = '//tr[not(.//table)]'
        case_dates = []
        for tr_elem in self.html.xpath(path):
            if tr_elem.xpath('''td/font[@size = '+1']'''):
                # If it's a date row...
                d_string = html.tostring(tr_elem, method='text', encoding='unicode')
                d = datetime.strptime(d_string.strip(), '%B %d, %Y').date()
            else:
                # See if it's a row with an opinion
                if tr_elem.xpath('./td[4]') and \
                        tr_elem.xpath('''./td[2]//@href[not(contains(., 'DecisionList'))]'''):
                    case_dates.append(d)
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '''//*[count(td)=4]/td[1]'''
        docket_numbers = []
        for elem in self.html.xpath(path):
            text_nodes = elem.xpath('.//text()')
            t = ', '.join(text_nodes)
            if re.search(r'No\.', t):
                docket_numbers.append(t)
        return docket_numbers
