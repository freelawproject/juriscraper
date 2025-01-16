from juriscraper.pacer import PacerSession, FreeOpinionReport, AppellateAttachmentPage , PossibleCaseNumberApi
from requests.cookies import RequestsCookieJar
from juriscraper.pacer.appellate_docket import AppellateDocketReport
import pickle
import csv

class EgressPacerSession(PacerSession):

    def __init__(
        self, cookies=None, username=None, password=None, client_code=None
    ):
        super().__init__(cookies, username, password, client_code)
        self.proxies = {
            "http": "http://localhost:9090/",
        }
        self.headers["X-WhSentry-TLS"] = "true"

    def _prepare_login_request(self, url, *args, **kwargs):
        return super(PacerSession, self).post(
            self._change_protocol(url), **kwargs
        )

    def _change_protocol(self, url: str) -> str:
        """Converts a URL from HTTPS to HTTP protocol.

        By default, HTTP clients create a CONNECT tunnel when a proxy is
        configured and the target URL uses HTTPS. This doesn't provide the
        security benefits of initiating TLS from the proxy. To address this,
        Webhook Sentry supports a unique approach. You should:

        1. Change the protocol in the URL to HTTP.
        2. Set the `X-WhSentry-TLS` header in your request to instruct Webhook
           Sentry to initiate TLS with the target server.

        https://github.com/juggernaut/webhook-sentry?tab=readme-ov-file#https-target

        Args:
            url (str): The URL to modify.

        Returns:
            str: The URL with the protocol changed from HTTPS to HTTP.
        """
        return url.replace("https://", "http://")

    def post(self, url, *args, **kwargs):
        return super().post(self._change_protocol(url), **kwargs)

    def get(self, url, *args, **kwargs):
        return super().get(self._change_protocol(url), **kwargs)

def log_into_pacer(
    username: str,
    password: str,
    client_code: str | None = None,
) -> RequestsCookieJar:
    s = PacerSession(
        username=username,
        password=password,
        client_code=client_code,
    )
    s.login()
    return s.cookies

