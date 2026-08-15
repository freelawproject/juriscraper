from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.WebDriven import WebDriven


class OpinionSiteLinearWebDriven(OpinionSiteLinear, WebDriven):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        WebDriven.__init__(self, args, kwargs)

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close_session()

    def __del__(self):
        self.close_webdriver_session()
