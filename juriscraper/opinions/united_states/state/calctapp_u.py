from juriscraper.opinions.united_states.state import calctapp_1st


class Site(calctapp_1st.Site):
    court_code = "S"
    division = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.courts.ca.gov/cms/npopinions.htm"
        self.court_id = self.__module__
        self.status = "Unpublished"
        self.should_have_results = True
