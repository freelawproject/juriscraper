#  Scraper for Florida Supreme Court
# CourtID: fla
# Court Short Name: fla
# Author: Andrei Chelaru
# Reviewer:
# Date created: 21 July 2014


from datetime import date, datetime
import re

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.year = date.today().year
        self.regex = re.compile("(SC\d+-\d+)(.*)")
        self.base_path = "//h2[contains(., '{y}')]".format(y=self.year)
        self.url = 'http://www.floridasupremecourt.org/decisions/opinions.shtml'

    def _get_case_names(self):
        path = "{base}/text()/following::ul[1]//li".format(base=self.base_path)
        return map(self._return_case_name, self.html.xpath(path))

    def _return_case_name(self, e):
        path = ".//a"
        case_name = []
        for a in e.xpath(path):
            text = ' '.join(a.xpath(".//text()[not(contains(., 'Notice'))]"))
            try:
                case_name.append(self.regex.search(text).group(2))
            except AttributeError:
                pass
        return ' and '.join(case_name)

    def _get_download_urls(self):
        path = "{base}/text()/following::ul[1]//li//a[1]/@href".format(base=self.base_path)
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        case_dates = []
        for e in self.html.xpath(self.base_path):
            text = e.xpath("./text()")[0]
            text = re.sub('Releases for ', '', text)
            case_date = datetime.strptime(text.strip(), '%B %d, %Y').date()
            case_dates.extend([case_date] * int(e.xpath("count(./following::ul[1]//li)")))
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = "{base}/text()/following::ul[1]//li".format(base=self.base_path)
        return map(self._return_docket_number, self.html.xpath(path))

    def _return_docket_number(self, e):
        path = ".//a/text()[not(contains(., 'Notice'))]"
        docket_number = []
        for cn in e.xpath(path):
            # cn = ''.join(cn.split())
            match = self.regex.search(cn)
            try:
                docket_number.append(match.group(1))
            except AttributeError:
                pass
        return ', '.join(docket_number)

    def _download_backwards(self):
        self.url = 'http://www.floridasupremecourt.org/decisions/{y}/index.shtml'.format(y=self.year)
        self.html = self._download()