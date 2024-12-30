from juriscraper.opinions.united_states.state import cal


class Site(cal.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.courts.ca.gov/cms/npopinions.htm"
        self.court_id = self.__module__
        self.status = "Unpublished"
