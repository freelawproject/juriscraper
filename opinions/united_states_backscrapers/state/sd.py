# Author: Michael Lissner
# Date created: 2013-06-11

import re
from datetime import date
from datetime import datetime
from lxml import html
from selenium import webdriver
from time import sleep
from juriscraper.GenericSite import GenericSite
from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.sdjudicial.com/sc/scopinions.aspx'

    def _get_download_urls(self):
        path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]//a[2]/@href'
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]/td[2]/text()'
        case_names = []
        for s in self.html.xpath(path):
            try:
                case_name = re.search('(.*)(\d{4} S\.?D\.? \d{1,4})', s, re.MULTILINE).group(1)
                case_names.append(titlecase(case_name.lower()))
            except AttributeError:
                print "AttributeError on: %s" % s
                if 'myrl' in s.lower() and self.year == 2000:
                    case_names.append('Lends His Horse v. Myrl & Roy')
                elif 'springer' in s.lower() and self.year == 2000:
                    case_names.append('State v. Springer-Ertl')
                elif 'formatting provided courtesy' in s.lower() and self.year == 2000:
                    case_names.append('Lois F. Henry v. Harold L. Henry')
                elif 'spec. v. avera' in s.lower() and self.year == 2001:
                    case_names.append('Drs., Residents, and Orth. Surg. Spec. v. Avera St. Luke')
                elif 'clausen' in s.lower() and self.year == 2003:
                    case_names.append('Kelly Clausen v. Northern Plains Recycling, Fireman')
                elif 'burkhart' in s.lower() and self.year == 2003:
                    case_names.append('Burkhart v. Lillehaug and Lillihaug')
                elif 'bennett' in s.lower() and self.year == 2003:
                    case_names.append('State of South Dakota, ex rel., Megan Bennett v. Thomas G. Peterson')
                elif 'duane' in s.lower() and self.year == 2004:
                    case_names.append('State of South Dakota v. Duane J. St. John')
                elif 'square' in s.lower() and self.year == 2005:
                    case_names.append('Town Square Limited Partnership v. Clay County Board of Equalization')
                else:
                    raise AttributeError
        return case_names

    def _get_case_dates(self):
        path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]/td[1]/@uv'
        return [datetime.strptime(date_string, '%m/%d/%Y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]//a[2]/@href'
        docket_numbers = []
        for url in self.html.xpath(path):
            try:
                # New style: easy
                docket_numbers.append(re.search('(\d+).pdf', url).group(1))
            except AttributeError:
                docket_numbers.append(None)
        return docket_numbers

    def _get_neutral_citations(self):
        path = '//tr[contains(@id, "ctl00xmainCopyxWGOpinions_r")]/td[2]/text()'
        neutral_cites = []
        for s in self.html.xpath(path):
            try:
                neutral_cite = re.search('(.*)(\d{4} S\.?D\.? \d{1,4})', s, re.MULTILINE).group(2)
                neutral_cites.append(titlecase(neutral_cite))
            except AttributeError:
                if 'myrl' in s.lower() and self.year == 2000:
                    neutral_cites.append('2000 SD 146')
                elif 'springer' in s.lower() and self.year == 2000:
                    neutral_cites.append('2000 SD 56')
                elif 'formatting provided courtesy' in s.lower() and self.year == 2000:
                    neutral_cites.append('2000 SD 4')
                elif 'spec. v. avera' in s.lower() and self.year == 2001:
                    neutral_cites.append('2001 SD 9')
                elif 'clausen' in s.lower() and self.year == 2003:
                    neutral_cites.append('2003 SD 63')
                elif 'burkhart' in s.lower() and self.year == 2003:
                    neutral_cites.append('2003 SD 62')
                elif 'bennett' in s.lower() and self.year == 2003:
                    neutral_cites.append('2003 SD 16')
                elif 'duane' in s.lower() and self.year == 2004:
                    neutral_cites.append('2004 SD 15')
                elif 'square' in s.lower() and self.year == 2005:
                    neutral_cites.append('2005 SD 99')
                else:
                    raise AttributeError
        return neutral_cites

    def _download_backwards(self, year):
        self.year = year
        browser = webdriver.PhantomJS()
        browser.get(self.url)
        elems = browser.find_elements_by_class_name('igeb_ItemLabel')
        elem = [elem for elem in elems if elem.text == str(year)][0]
        elem.click()
        sleep(5)

        text = browser.page_source
        html_tree = html.fromstring(text)
        html_tree.make_links_absolute(self.url)

        remove_anchors = lambda url: url.split('#')[0]
        html_tree.rewrite_links(remove_anchors)

        self.html = html_tree
        self.status = 200
        browser.quit()
