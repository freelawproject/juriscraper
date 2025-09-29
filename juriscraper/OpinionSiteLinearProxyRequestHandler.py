import os

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class OpinionSiteLinearProxyRequestHandler(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _download(self, request_dict=None):
        USERNAME = os.environ.get("DECODO_USER")
        PASSWORD = os.environ.get("DECODO_PASSWORD")
        PROXY_ADDRESS = os.environ.get("DECODO_PROXY")
        PORT = os.environ.get("DECODO_PORT")
        proxy_values = [USERNAME, PASSWORD, PROXY_ADDRESS, PORT]
        if not all(proxy_values) and not self.test_mode_enabled():
            raise ValueError("Missing DECODO proxy environment variables")
        return super()._download(request_dict)
