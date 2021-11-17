from juriscraper.OpinionSite import OpinionSite
from juriscraper.WebDriven import WebDriven


class OpinionSiteWebDriven(OpinionSite, WebDriven):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        WebDriven.__init__(self, args, kwargs)

    def __del__(self):
        self.close_session()
        self.close_webdriver_session()
