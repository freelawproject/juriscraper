from juriscraper.OpinionSite import OpinionSite
import re
import time
from datetime import date


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.courtinfo.ca.gov/cgi-bin/opinions-blank.cgi?Courts=S'
        self.court_id = self.__module__

    def _get_case_names(self):
        case_names = []
        for name in self.html.xpath('//table/tr/td[3]/text()'):
            date_regex = re.compile(r' \d\d?\/\d\d?\/\d\d| filed')
            if 'P. v. ' in date_regex.split(name)[0]:
                case_names.append(date_regex.split(name)[0].replace("P. ", "People "))
            else:
                case_names.append(date_regex.split(name)[0])
        return case_names

    def _get_download_urls(self):
        return [t for t in self.html.xpath("//table/tr/td[2]/a/@href[contains(.,'PDF')]")]

    def _get_case_dates(self):
        dates = []
        for s in self.html.xpath('//table/tr/td[1]/text()'):
            s = s.strip()
            date_formats = ['%b %d %Y', '%b %d, %Y']
            for format in date_formats:
                try:
                    dates.append(date.fromtimestamp(time.mktime(time.strptime(s, format))))
                except ValueError:
                    pass
        return dates

    def _get_docket_numbers(self):
        return [t for t in self.html.xpath('//table/tr/td[2]/text()[1]')]

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)
