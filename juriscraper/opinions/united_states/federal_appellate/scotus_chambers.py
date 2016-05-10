import scotus_slip


class Site(scotus_slip.Site):
    CELLS = {
        'date': 1,
        'docket': 2,
        'name': 3,
        'revision': 4,
    }

    # Note that scotus_relating inherits from this class.
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = 'http://www.supremecourt.gov/opinions/in-chambers.aspx'
        self.back_scrape_url = 'http://www.supremecourt.gov/opinions/in-chambers/{}'
        self.back_scrape_iterable = range(5, 16)
        self.court_id = self.__module__

    def _get_precedential_statuses(self):
        return ['In-chambers'] * len(self.case_names)
