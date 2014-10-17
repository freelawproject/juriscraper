import scotus_chambers


class Site(scotus_chambers.Site):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://www.supremecourt.gov/opinions/relatingtoorders.aspx'
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        return ['Relating-to'] * len(self.case_names)

    def _get_summaries(self):
        return None
