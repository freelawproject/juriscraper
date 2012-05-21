from juriscraper.GenericSite import GenericSite
import time
from datetime import date


class in_supreme(GenericSite):
    def __init__(self):
        super(in_supreme, self).__init__()
        self.url = 'http://www.in.gov/judiciary/opinions/archsup.html'
        self.court_id = self.__module__

    def _get_case_names(self):
        return [e for e in self.html.xpath("//table/tr/td[3]/table/tr[4]//table/tr[position() > 1]/td[2]//a/text()")]

    def _get_download_urls(self):
        return [e for e in self.html.xpath("//table/tr/td[3]/table/tr[4]//table/tr[position() > 1]/td[2]//a/@href")]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath('//table/tr/td[3]/table/tr[4]//table/tr[position() > 1]/td[1]//font/text()'):
            val = date_string.strip()
            if val == '':
                dates.append('')
            else:
                dates.append(date.fromtimestamp(time.mktime(time.strptime(val, '%m/%d/%y'))))
        return dates

    def _get_lower_courts(self):
        return [e for e in self.html.xpath("//table/tr/td[3]/table/tr[4]//table/tr[position() > 1]/td[3]//font/text()")]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
