# Auth: ryee
# Review: mlr
# Date: 2013-04-26

from juriscraper.OpinionSite import OpinionSite
import time
from datetime import date
from lxml import html


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://courts.ms.gov/scripts/websiteX_cgi.exe/GetOpinion?Year=%s&Court=Supreme+Court&Submit=Submit' % date.today().year

    def _get_case_names(self):
        # This could be a very simple xpath, but alas, they have missing fields
        # for some cases. As a result, this xpath checks that the fields are
        # valid (following-sibling), and only grabs those cases.
        case_names = []
        for e in self.html.xpath('//tr[following-sibling::tr[1]/td[2][text()]]/td/b/a'):
            s = html.tostring(e, method='text', encoding='unicode')
            case_names.append(s)
        return case_names

    def _get_download_urls(self):
        path = '''//tr[following-sibling::tr[1]/td[2][text()]]/td/b/a/@href'''
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = '''//tr[following-sibling::tr[1]/td[2][text()]]/following-sibling::tr[1]/td[2]/text()'''
        dates = []
        for date_string in self.html.xpath(path):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(date_string, '%m/%d/%Y'))))
        return dates


    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        path = '''//tr[following-sibling::tr[1]/td[2][text()]]/following-sibling::tr[1]/td[1]/text()'''
        return list(self.html.xpath(path))

    def _download_backwards(self, year):
        self.url = 'http://courts.ms.gov/scripts/websiteX_cgi.exe/GetOpinion?Year=%s&Court=Supreme+Court&Submit=Submit' % year
        self.html = self._download()


