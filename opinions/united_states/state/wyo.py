from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import clean_string
import time
from datetime import date


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.courts.state.wy.us/Opinions.aspx'
        self.court_id = self.__module__

    def _get_case_names(self):
        appellants = self.html.xpath('//table/tr[@class="searchDataGridRow"]/td[3]/text()')
        appellees = self.html.xpath('//table/tr[@class="searchDataGridRow"]/td[4]/text()')
        return [' v. '.join(t) for t in zip(appellants, appellees)]

    def _get_download_urls(self):
        return [href for href in
                self.html.xpath('//table/tr[@class="searchDataGridRow"]/td[6]/a/@href')]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath('//table/tr[@class="searchDataGridRow"]/td[2]/span/text()'):
            dates.append(date.fromtimestamp(time.mktime(time.strptime(clean_string(date_string), '%B %d, %Y'))))
        return dates

    def _get_docket_numbers(self):
        return [e for e in self.html.xpath('//table/tr[@class="searchDataGridRow"]/td[5]/text()')]

    def _get_neutral_citations(self):
        return [e for e in self.html.xpath('//table/tr[@class="searchDataGridRow"]/td[1]/text()')]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)
