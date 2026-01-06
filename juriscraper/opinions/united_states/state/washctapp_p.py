from juriscraper.opinions.united_states.state import wash


class Site(wash.Site):
    crt_level = "C"
    pub_status = "PUB"
    name_td_index = 4
    type_td_index = 5

    # Example URL
    # https://www.courts.wa.gov/opinions/index.cfm?fa=opinions.byYear&fileYear=2025&crtLevel=C&pubStatus=PUB

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
