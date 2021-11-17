from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.WebDriven import WebDriven


class OpinionSiteLinearWebDriven(OpinionSiteLinear, WebDriven):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        WebDriven.__init__(self, args, kwargs)

    def __del__(self):
        self.close_session()
        self.close_webdriver_session()
