from juriscraper.opinions.united_states.state import cal


class Site(cal.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.courts.ca.gov/cms/npopinions.htm"
        self.court_id = self.__module__
        self.status = "Unpublished"

    def get_class_name(self):
        return "calctapp_u"

    def get_court_name(self):
        return "California Court of Appeals"
