import wash
from datetime import datetime


class Site(wash.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.parameters = {'courtLevel': 'C',
                           'pubStatus': 'PUB',
                           'beginDate': '01/01/2012',
                           'endDate': '01/01/2050',
                           'SType': 'Phrase',
                           'SValue': ''}

    def _get_case_names(self):
        path = "//table[@class = 'listTable']/tr/td[4]/text()"
        return list(self.html.xpath(path))
