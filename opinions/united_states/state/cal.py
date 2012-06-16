from GenericSite import GenericSite
import re
import time
from datetime import date


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.courtinfo.ca.gov/cgi-bin/opinions-blank.cgi?Courts=S'
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for name in self.html.xpath('//table/tr/td[3]/text()'):
            date_regex = re.compile(r' \d\d?\/\d\d?\/\d\d| filed')
            case_names.append(date_regex.split(name)[0])
        return case_names

    def _get_download_urls(self):
        return [t for t in self.html.xpath("//table/tr/td[2]/a/@href[contains(.,'PDF')]")]

    def _get_case_dates(self):
        dates = []
        for s in self.html.xpath('//table/tr/td[1]/text()'):
            s = s.strip()
            dates.append(date.fromtimestamp(time.mktime(time.strptime(s, '%b %d %Y'))))
        return dates

    def _get_docket_numbers(self):
        return [t for t in self.html.xpath('//table/tr/td[2]/text()[1]')]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)
