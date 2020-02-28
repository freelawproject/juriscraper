from juriscraper.opinions.united_states.state import nm


class Site(nm.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://nmonesource.com/nmos/nmca/en/nav_date.do?%s" % self.IFRAME
        )
