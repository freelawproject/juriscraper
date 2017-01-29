"""
Scraper for Indiana Supreme Court archive before 6/6/2005
CourtID: ind
Court Short Name: Ind.
Auth: Mike Lissner <mike@freelawproject.org>
Reviewer:
History:
    2014-09-03: Renamed to ind_2005.py by janderse
"""
from juriscraper.OpinionSite import OpinionSite

import time
from datetime import date
from lxml import html


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.in.gov/judiciary/opinions/previous/archsup.html'
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath("//table/tr/td[1]/font/a/text()")]

    def _get_case_dates(self):
        dates = []
        for link_string in self.html.xpath('//table/tr/td[4]/font/a/@href'):
            date_string = link_string.split('/')[-1].split('.')[0][:-2]
            if date_string == '12319701-fs':
                # special case (there's always *one*)
                dates.append(date.fromtimestamp(
                    time.mktime(time.strptime('123197', '%m%d%y'))))
            elif len(date_string) == 4:
                dates.append(date.fromtimestamp(
                    time.mktime(time.strptime(date_string + '98', '%m%d%y'))))
            elif len(date_string) == 5:
                dates.append(date.fromtimestamp(
                    time.mktime(time.strptime('0' + date_string, '%m%d%y'))))
            elif len(date_string) == 6:
                dates.append(date.fromtimestamp(
                    time.mktime(time.strptime(date_string, '%m%d%y'))))
            else:
                print(date_string)
        return dates

    def _get_download_urls(self):
        return [s for s in self.html.xpath("//table/tr/td[4]/font/a/@href")]

    def _get_docket_numbers(self):
        return [html.tostring(e, method='text')
                    for e in self.html.xpath("//table/tr/td[2]")]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
