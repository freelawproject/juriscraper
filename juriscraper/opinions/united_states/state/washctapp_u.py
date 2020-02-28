from juriscraper.opinions.united_states.state import washctapp_p


class Site(washctapp_p.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.courtLevel = "C"
        self.pubStatus = "UNP"
        self._set_parameters()

    def _get_precedential_statuses(self):
        return ["Unpublished"] * len(self.case_names)
