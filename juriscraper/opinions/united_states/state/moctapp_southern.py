import mo


class Site(mo.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__

    def url_base(self):
        return 'Southern'

    def _get_divisions(self):
        return ['Southern Distr.'] * len(self.cases)
