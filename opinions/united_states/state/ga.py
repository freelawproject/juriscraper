#  Scraper for Georgia Supreme Court
# CourtID: ga
# Court Short Name: ga
# Author: Andrei Chelaru
# Reviewer: mlr
# Date created: 25 July 2014


from datetime import date, datetime
from juriscraper.lib.string_utils import titlecase
import re

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        d = date.today()
        self.base_path = "//p[contains(., 'SUMMARIES')]"
        self.regex = re.compile("(S\d{2}.*\d{4})\.?(.*)")
        self.url = 'http://www.gasupreme.us/sc-op/opinion_lists/{year}_opinions.php'.format(year=d.year)

    def _get_case_names(self):
        path = "{base}/following::ul[1]//li//a[1]/text()".format(base=self.base_path)
        return [titlecase(self.regex.search(s).group(2).lower()) for s in self.html.xpath(path)]

    def _get_download_urls(self):
        path = "{base}/following::ul[1]//li//a[1]/@href".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        case_dates = []
        for e in self.html.xpath(self.base_path):
            text = ' '.join(e.xpath(".//text()[not(contains(., 'SUMMARIES'))]"))
            text = re.sub('-', '', text)
            case_date = datetime.strptime(text.strip(), '%B %d, %Y').date()
            case_dates.extend([case_date] * int(e.xpath("count(./following::ul[1]//li)")))
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "{base}/following::ul[1]//li//a[1]/text()".format(base=self.base_path)
        return [self.regex.search(e).group(1) for e in self.html.xpath(path)]
