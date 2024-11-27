# added by hitesh for publish in parts case of court of appleas
from juriscraper.opinions.united_states.state import washctapp_p


class Site(washctapp_p.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"https://www.courts.wa.gov/opinions/index.cfm?fa=opinions.byYear&fileYear={self.year}&crtLevel=C&pubStatus=PAR"
        self.status = "Published in Part"

    def get_class_name(self):
        return "washctapp_p_inpart"
