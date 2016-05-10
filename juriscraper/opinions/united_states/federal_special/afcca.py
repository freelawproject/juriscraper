"""Scraper for the Air Force Court of Criminal Appeals
CourtID: afcca
Court Short Name: Air Force Court of Criminal Appeals
Reviewer: mlr
History:
    15 Sep 2014: Created by Jon Andersen
"""

from juriscraper.OpinionSite import OpinionSite
import time
from datetime import date


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://afcca.law.af.mil/content/opinions.php%%3Fyear=%d&sort=pub&tabid=3.html' % (date.today().year,)
        self.court_id = self.__module__
        self.back_scrape_iterable = range(2013, 2002 - 1, -1)

    def _get_case_dates(self):
        path = "//table[@width='600']//tr[td[@class='stdRowText']]/td[5]/text()"
        return [date.fromtimestamp(
            time.mktime(time.strptime(date_string, '%d %b %y'))) for
                date_string in self.html.xpath(path)]

    def _get_case_names(self):
        path = "//table[@width='600']//tr[td[@class='stdRowText']]/td[2]/a/text()"
        return [text for text in self.html.xpath(path)]

    def _get_download_urls(self):
        path = "//table[@width='600']//tr[td[@class='stdRowText']]/td[2]/a/@href"
        return [text for text in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = "//table[@width='600']//tr[td[@class='stdRowText']]/td[3]/text()"
        return [("ACM " + text) for text in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        path = "//table[@width='600']//tr[td[@class='stdRowText']]/td[4]/div/text()"
        statuses = []
        for s in self.html.xpath(path):
            if 'Unpublished' in s:
                statuses.append('Unpublished')
            else:
                statuses.append('Published')
        return statuses

    def _download_backwards(self, year):
        self.url = 'http://afcca.law.af.mil/content/opinions.php%%3Fyear=%d&sort=pub&tabid=3.html' \
                   % year
        self.html = self._download()
