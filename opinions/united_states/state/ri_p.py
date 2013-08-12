"""Scraper for the Rhode Island Supreme Court
CourtID: ri
Court Short Name: R.I.
Author: Brian W. Carver
Date created: 2013-08-10
"""

import re
from datetime import date
from datetime import datetime
from lxml import html

from juriscraper.GenericSite import GenericSite


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        #This page provides the Supreme Court's published opinions.
        #Another page provides the Supreme Court's unpublised orders.
        #Backscrapers are possible back to the (1999-2000) term.
        self.url = 'http://www.courts.ri.gov/Courts/SupremeCourt/Opinions/Opinions%20%282012-2013%29.aspx'

    def _get_download_urls(self):
        path = "//table[@id = 'onetidDoclibViewTbl0']/tr[position() > 1]/td/a[child::span]/@href"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        case_names = []
        path = "//table[@id = 'onetidDoclibViewTbl0']/tr[position() > 1]/td/a/span/text()"
        #Could an easier regex do the same thing? Perhaps, but this works.
        expression = '(\s*.*)(,? No\. *\d*-\d*.[^(.]*|,? Nos\..*\d\d*-\d*.[^(.]*|,? \d*-\d*.[^(.]*|,? No\.\d*-\d*[^(.]*)(\(.*)'
        for s in self.html.xpath(path):
            case_name = re.search(expression, s, re.MULTILINE).group(1)
            #Chopping off some docket numbers that get mixed in.
            case_name = case_name.split(', Nos.', 1)[0].strip()
            case_names.append(case_name)
        return case_names

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_case_dates(self):
        case_dates = []
        path = "//table[@id = 'onetidDoclibViewTbl0']/tr[position() > 1]/td/a/span/text()"
        expression = '(.*)(,? No\. *\d*-\d*.[^(.]*|,? Nos\..*\d\d*-\d*.[^(.]*|,? \d*-\d*.[^(.]*|,? No\.\d*-\d*[^(.]*)(\(.*)'
        for s in self.html.xpath(path):
            date_string = re.search(expression, s, re.MULTILINE).group(3)
            #Both some whitespace and surrounding parentheses must be removed.
            date_string = date_string.strip()[1:-1]
            case_dates.append(datetime.strptime(date_string, '%B %d, %Y').date())
        return case_dates

    def _get_docket_numbers(self):
        docket_numbers = []
        path = "//table[@id = 'onetidDoclibViewTbl0']/tr[position() > 1]/td/a/span/text()"
        expression = '(.*)(,? No\. *\d*-\d*.[^(.]*|,? Nos\..*\d\d*-\d*.[^(.]*|,? \d*-\d*.[^(.]*|,? No\.\d*-\d*[^(.]*)(\(.*)'
        for s in self.html.xpath(path):
            dockets = re.search(expression, s, re.MULTILINE).group(2)
            #This page lists these about five different ways, normalizing:
            dockets = dockets[2:].strip('No.').strip('s.').strip()
            docket_numbers.append(dockets)
        return docket_numbers

    def _get_summaries(self):
        summaries = []
        path = "//table[@id = 'onetidDoclibViewTbl0']/tr[position() > 1]/td/div[@class = 'styleDescription']"
        for e in self.html.xpath(path):
            summaries.append(html.tostring(e, method='text', encoding='unicode'))
        return summaries
