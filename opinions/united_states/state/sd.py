# Author: Michael Lissner
# Date created: 2013-06-11
# Revised: 2013-08-06 by Brian Carver

import re
from datetime import date
from datetime import datetime

from juriscraper.GenericSite import GenericSite
from juriscraper.lib.string_utils import titlecase


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.sdjudicial.com/Supreme_Court/opinions.aspx'

    def _get_download_urls(self):
        path ="//table[@id = 'ContentPlaceHolder1_PageContent_gvOpinions']//a/@href[contains(.,'pdf')]"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path ="//table[@id = 'ContentPlaceHolder1_PageContent_gvOpinions']//tr[position() > 1]/td/a[contains(@href, 'pdf')]/text()"
        case_names = []
        for s in self.html.xpath(path):
            case_name = re.search('(.*)(\d{4} S\.?D\.? \d{1,4})', s, re.MULTILINE).group(1)
            case_names.append(titlecase(case_name.upper()))
        return case_names

    def _get_case_dates(self):
        path = "//table[@id = 'ContentPlaceHolder1_PageContent_gvOpinions']//tr[position() >1]/td[1]/text()"
        return [datetime.strptime(date_string, '%m/%d/%Y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_neutral_citations(self):
        path = "//table[@id = 'ContentPlaceHolder1_PageContent_gvOpinions']//tr[position() > 1]/td/a[contains(@href, 'pdf')]/text()"
        neutral_cites = []
        for s in self.html.xpath(path):
            neutral_cite = re.search('(.*)(\d{4} S\.?D\.? \d{1,4})', s, re.MULTILINE).group(2)
            # Make the citation SD instead of S.D. The former is a neutral cite, the latter, the South Dakota Reporter
            neutral_cites.append(neutral_cite.replace('.', ''))
        return neutral_cites
