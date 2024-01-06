from juriscraper.OralArgumentSiteLinear import OralArgumentSiteLinear
from juriscraper.WebDriven import WebDriven


class OralArgumentSiteLinearWebDriven(OralArgumentSiteLinear, WebDriven):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        WebDriven.__init__(self, args, kwargs)

    async def __aexit__(self):
        await self.close_session()

    def __del__(self):
        self.close_webdriver_session()
