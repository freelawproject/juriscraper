import scotus_chambers


class Site(scotus_chambers.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.supremecourt.gov/opinions/relatingtoorders.aspx'
        self.court_id = self.__module__
        self.back_scrape_url = 'http://www.supremecourt.gov/opinions/relatingtoorders/{}'

    def _get_precedential_statuses(self):
        return ['Relating-to'] * len(self.case_names)
