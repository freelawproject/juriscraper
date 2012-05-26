import ca_supreme


class Site(ca_supreme.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = (
        'http://www.courtinfo.ca.gov/cms/npopinions.htm')
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        statuses = []
        for opinion in self.html.xpath('//table/tr/td[3]/text()'):
            statuses.append('Unpublished')
        return statuses
