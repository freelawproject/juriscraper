from juriscraper.opinions.united_states.state import mo


class Site(mo.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url_slug = "Western"
        self.url = self.build_url()

    def _get_divisions(self):
        return ['Western Dist.'] * len(self.cases)
