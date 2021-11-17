from juriscraper.opinions.united_states.state import nm


class Site(nm.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            f"https://nmonesource.com/nmos/nmca/en/nav_date.do?{self.IFRAME}"
        )
