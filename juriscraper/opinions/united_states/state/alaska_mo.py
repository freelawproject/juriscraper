from juriscraper.opinions.united_states.state import alaska


class Site(alaska.Site):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://appellate-records.courts.alaska.gov/CMSPublic/Home/MOJOpinions?isCOA=False"
        self.opinion_type="minute order"

    def get_class_name(self):
        return "alaska_mo"
