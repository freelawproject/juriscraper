from juriscraper.opinions.united_states.state import mo


class Site(mo.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url_slug = "Eastern"
        self.url = self.build_url()

    def _get_divisions(self):
        return ["Eastern Dist."] * len(self.cases)
