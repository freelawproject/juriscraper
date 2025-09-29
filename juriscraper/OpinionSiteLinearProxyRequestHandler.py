from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.ProxyRequestHandler import ProxyRequestHandler


class OpinionSiteLinearProxyRequestHandler(
    OpinionSiteLinear, ProxyRequestHandler
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
