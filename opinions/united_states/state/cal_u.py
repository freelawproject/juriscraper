import cal_supreme


class Site(cal_supreme.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.courtinfo.ca.gov/cms/npopinions.htm'
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        return ['Unpublished'] * len(self.case_names)
