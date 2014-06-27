"""
Scraper for Maryland
CourtID: md
Court Short Name: MD
Author: Andrei Chelaru
Date created: 06/27/2014
"""


from juriscraper.OpinionSite import OpinionSite

import time
from datetime import date


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.mdcourts.gov/cgi-bin/indexlist.pl?court=coa' \
                    '&year={current_year}&order=bydate&submit=Submit'.format(current_year=date.today().year)
        self.court_id = self.__module__

    def _get_download_urls(self):
        path = "//table//tr/td[1]//@href[contains(.,'pdf')]"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = '//table//tr/td[5]/font/text()'
        case_names = []
        for s in self.html.xpath(path):
            case_names.append(s.split('(')[0])
        return case_names

    def _get_judges(self):
        path = '//table//tr/td[4]/font/text()'
        judge_names = []
        for s in self.html.xpath(path):
            judge_names.append(s.split('(')[0])
        return judge_names

    def _get_case_dates(self):
        path = '//table//tr/td[3]/font/text()'
        return [date.fromtimestamp(time.mktime(time.strptime(date_string.replace(' ', ''), '%Y-%m-%d')))
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '//table//tr/td[1]//text()'
        return list(self.html.xpath(path))
    
    def _get_neutral_citations(self):
        path = '//table//tr/td[2]/font/text()'
        return list(self.html.xpath(path))