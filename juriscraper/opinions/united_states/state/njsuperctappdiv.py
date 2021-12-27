from juriscraper.opinions.united_states.state import nj


class Site(nj.Site):
    """Human web interface: http://www.judiciary.state.nj.us/attorneys/opinions.html#Unpublished_Appellate"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.case_types = ["Published_Appellate", "Unpublished_Appellate"]
