from juriscraper.OpinionSite import OpinionSite
from datetime import datetime


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.courts.wa.gov/opinions/index.cfm?fa=opinions.processSearch'
        self.parameters = {'courtLevel': 'S',
                           'pubStatus': 'All',
                           'beginDate': '01/01/2012',
                           'endDate': '01/01/2050',
                           'SType': 'Phrase',
                           'SValue': ''}
        self.method = 'POST'

    def _get_case_names(self):
        path = "//table[@class = 'listTable']/tr/td[3]/text()"
        return list(self.html.xpath(path))

    def _get_docket_numbers(self):
        path = "//table[@class = 'listTable']/tr/td[2]/a/text()"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "//table[@class = 'listTable']/tr/td[1]/text()"
        return [datetime.strptime(date_string, '%b. %d, %Y').date()
                for date_string in self.html.xpath(path)]

    def _get_download_urls(self):
        path = "//table[@class = 'listTable']/tr/td[2]/a[2]/@href"
        return list(self.html.xpath(path))

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

