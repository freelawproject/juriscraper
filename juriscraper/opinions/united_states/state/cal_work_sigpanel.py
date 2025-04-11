from juriscraper.opinions.united_states.state import cal_work


class Site(cal_work.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url="https://www.dir.ca.gov/wcab/wcab_panel.htm"

    def get_class_name(self):
        return "cal_work_sigpanel"
