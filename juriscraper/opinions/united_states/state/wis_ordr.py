from juriscraper.opinions.united_states.state import wis


class Site(wis.Site):
    division = 2
    days_interval = 200

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.wicourts.gov/supreme/scorder.jsp"


    def get_class_name(self):
        return "wis_ordr"
