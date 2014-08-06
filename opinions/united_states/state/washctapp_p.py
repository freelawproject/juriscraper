import wash


class Site(wash.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.pubStatus = 'PUB'
        self._set_parameters()

    def _get_case_names(self):
        path = "{base}/td[4]/text()".format(base=self.base)
        return list(self.html.xpath(path))
