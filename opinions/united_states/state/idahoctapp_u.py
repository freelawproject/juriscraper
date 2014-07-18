import idaho_civil


class Site(idaho_civil.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.isc.idaho.gov/appeals-court/coaunpublished'
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        return ["Unpublished"] * len(self.case_names)
