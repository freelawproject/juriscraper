from juriscraper.opinions.united_states.state import wash


class Site(wash.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.courtLevel = "C"
        self.pubStatus = "PUB"
        self._set_parameters()

    def _get_case_names(self):
        path = f"{self.base}/td[4]/text()"
        return list(self.html.xpath(path))
