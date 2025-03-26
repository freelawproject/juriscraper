import json
import re
from urllib.parse import unquote

import httpx

from ..lib.exceptions import PacerLoginException
from ..lib.html_utils import get_html_parsed_text, get_xml_parsed_text
from ..lib.log_tools import make_default_logger
from ..pacer.utils import is_pdf, is_text

logger = make_default_logger()


def check_if_logged_in_page(content: bytes) -> bool:
    """Is this a valid HTML page from PACER?

    Check if the data in 'content' is from a valid PACER page or valid PACER
    XML document, or if it's from a page telling you to log in or informing you
    that you're not logged in.
    :param content: The data to test, of type bytes. This uses bytes to avoid
    converting data to text using an unknown encoding. (see #564)
    :return boolean: True if logged in, False if not.
    """

    valid_case_number_query = (
        b"<case number=" in content
        or b"<request number=" in content
        or b'id="caseid"' in content
        or b"Cost: " in content
    )
    no_results_case_number_query = re.search(b"<message.*Cannot find", content)
    sealed_case_query = re.search(b"<message.*Case Under Seal", content)
    if any(
        [
            valid_case_number_query,
            no_results_case_number_query,
            sealed_case_query,
        ]
    ):
        not_logged_in = re.search(b"text.*Not logged in", content)
        if not_logged_in:
            # An unauthenticated PossibleCaseNumberApi XML result. Simply
            # continue onwards. The complete result looks like:
            # <request number='1501084'>
            #   <message text='Not logged in.  Please refresh this page.'/>
            # </request>
            # An authenticated PossibleCaseNumberApi XML result.
            return False
        else:
            return True

    # Detect if we are logged in. If so, no need to do so. If not, we login
    # again below.
    found_district_logout_link = b"/cgi-bin/login.pl?logout" in content
    found_appellate_logout_link = b"InvalidUserLogin.jsp" in content

    # A download confirmation page doesn't contain a logout link but we're
    # logged into.
    is_a_download_confirmation_page = b"Download Confirmation" in content
    # When looking for a download confirmation page sometimes an appellate
    # attachment page is returned instead, see:
    # https://ecf.ca8.uscourts.gov/n/beam/servlet/TransportRoom?servlet=ShowDoc&pacer=i&dls_id=00802251695
    appellate_attachment_page = (
        b"Documents are attached to this filing" in content
    )
    # Sometimes the document is completely unavailable and an error message is
    # shown, see:
    # https://ecf.ca11.uscourts.gov/n/beam/servlet/TransportRoom?servlet=ShowDoc/009033568259
    appellate_document_error = (
        b"The requested document cannot be displayed" in content
    )
    if any(
        [
            found_district_logout_link,
            found_appellate_logout_link,
            is_a_download_confirmation_page,
            appellate_attachment_page,
            appellate_document_error,
        ]
    ):
        # A normal HTML page we're logged into.
        return True

    return False


class PacerSession(httpx.AsyncClient):
    """
    Extension of httpx.AsyncClient to handle PACER oddities making it easier
    for folks to just POST data to PACER endpoints/apis.

    Also includes utilities for logging into PACER and re-logging in when
    sessions expire.
    """

    LOGIN_URL = "https://pacer.login.uscourts.gov/services/cso-auth"

    def __init__(
        self,
        cookies=None,
        username=None,
        password=None,
        client_code=None,
        user_agent="Juriscraper",
        **kwargs,
    ):
        """
        Instantiate a new PACER API Session with some Juriscraper defaults
        :param cookies: an optional httpx.Cookies object with cookies for the session
        :param username: a PACER account username
        :param password: a PACER account password
        :param client_code: an optional PACER client code for the session
        """
        kwargs.setdefault("http2", True)
        kwargs.setdefault("follow_redirects", True)
        super().__init__(**kwargs)
        self.user_agent = user_agent
        self.headers["User-Agent"] = self.user_agent
        self.headers["Referer"] = "https://external"  # For CVE-001-FLP.
        self.verify = False

        if cookies:
            assert not isinstance(cookies, str), (
                "Got str for cookie parameter. Did you mean "
                "to use the `username` and `password` kwargs?"
            )
            self.cookies = cookies

        self.username = username
        self.password = password
        self.client_code = client_code
        self.additional_request_done = False

    async def get(self, url, auto_login=True, **kwargs):
        """Overrides httpx.AsyncClient.get with session retry logic.

        :param url: url string to GET
        :param auto_login: Whether the auto-login procedure should happen.
        :return: httpx.Response
        """
        if "timeout" not in kwargs:
            kwargs.setdefault("timeout", 300)

        r = await super().get(url, **kwargs)

        if b"This user has no access privileges defined." in r.content:
            # This is a strange error that we began seeing in CM/ECF 6.3.1 at
            # ILND. You can currently reproduce it by logging in on the central
            # login page, selecting "Court Links" as your destination, and then
            # loading: https://ecf.ilnd.uscourts.gov/cgi-bin/WrtOpRpt.pl
            # The solution when this error shows up is to simply re-run the get
            # request, so that's what we do here. PACER needs some frustrating
            # and inelegant hacks sometimes.
            r = await super().get(url, **kwargs)
        if auto_login:
            updated = await self._login_again(r)
            if updated:
                # Re-do the request with the new session.
                r = await super().get(url, **kwargs)
                # Do an additional check of the content returned.
                await self._login_again(r)
        return r

    async def post(self, url, data=None, json=None, auto_login=True, **kwargs):
        """
        Overrides httpx.AsyncClient.post with PACER-specific fun.

        Will automatically convert data dict into proper multi-part form data
        and pass to the files parameter instead.

        Will set a timeout of 300 if not provided.

        All other uses or parameters will pass through untouched
        :param url: url string to post to
        :param data: post data
        :param json: json object to post
        :param auto_login: Whether the auto-login procedure should happen.
        :param kwargs: assorted keyword arguments
        :return: httpx.Response
        """
        kwargs.setdefault("timeout", 300)

        if data:
            pacer_data = self._prepare_multipart_form_data(data)
            kwargs.update({"files": pacer_data})
        else:
            kwargs.update({"data": data, "json": json})

        r = await super().post(url, **kwargs)
        if auto_login:
            updated = await self._login_again(r)
            if updated:
                # Re-do the request with the new session.
                return await super().post(url, **kwargs)
        return r

    async def head(self, url, **kwargs):
        """
        Overrides httpx.AsyncClient.head with a default timeout parameter.

        :param url: url string upon which to do a HEAD request
        :param kwargs: assorted keyword arguments
        :return: httpx.Response
        """
        kwargs.setdefault("timeout", 300)
        return await super().head(url, **kwargs)

    @staticmethod
    def _prepare_multipart_form_data(data):
        """
        Transforms a data dictionary into the multi-part form data that PACER
        expects as the POST body
        :param data: dict of data to transform
        :return: dict with values wrapped into tuples like:(None, <value>)
        """
        output = dict()
        for key in data:
            output[key] = (None, data[key])
        return output

    @staticmethod
    def _get_view_state(r):
        """Get the viewState parameter of the form

        This is an annoying thing we have to do. The login flow has three
        requests that you make and each requires the view state from the one
        prior. Thus, we capture that viewState each time and submit it during
        each of the next submissions.

        The HTML takes the form of:

        <input type="hidden" name="javax.faces.ViewState"
               id="j_id1:javax.faces.ViewState:0"
               value="some-long-value-here">

        :param r: A httpx.Response object
        :return The value of the "value" attribute of the ViewState input
        element.
        """
        tree = get_html_parsed_text(r.content)
        xpath = (
            '//form[@id="loginForm"]//input['
            '    @name="javax.faces.ViewState"'
            "]/@value"
        )
        return tree.xpath(xpath)[0]

    @staticmethod
    def _get_xml_view_state(r):
        """Same idea as above, but sometimes PACER returns XML so we parse
        that instead of the HTML.

        Here's a sample of the XML:

        <partial-response id="j_id1">
          <changes>
            <update id="regmsg:bpmConfirm">
              <![CDATA[<button id="regmsg:bpmConfirm" name="regmsg:bpmConfirm" class="ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only" onclick="PrimeFaces.ab({s:&quot;regmsg:bpmConfirm&quot;,pa:[{name:&quot;dialogName&quot;,value:&quot;redactionDlg&quot;}]});return false;" style="margin-right: 20px;" type="submit"><span class="ui-button-text ui-c">Continue</span></button><script id="regmsg:bpmConfirm_s" type="text/javascript">PrimeFaces.cw("CommandButton","widget_regmsg_bpmConfirm",{id:"regmsg:bpmConfirm"});</script>]]>
            </update>
            <update id="loginForm:pclLoginMessages">
              <![CDATA[<div id="loginForm:pclLoginMessages" class="ui-messages ui-widget" style="font-size: 0.85em;" aria-live="polite"></div>]]>
            </update>
            <update id="j_id1:javax.faces.ViewState:0"><![CDATA]]>
            </update>
          </changes>
        </partial-response>
        """
        tree = get_xml_parsed_text(r.content)
        xpath = "//update[@id='j_id1:javax.faces.ViewState:0']/text()"
        return tree.xpath(xpath)[0]

    async def _prepare_login_request(
        self, url, data, headers, *args, **kwargs
    ):
        """Prepares and sends a POST request for login purposes.

        This internal helper function constructs a POST request to the provided URL
        using the given headers and data. It sets a timeout of 60 seconds for the
        request.

        :param url: The URL of the login endpoint.
        :param data: A dictionary containing login credentials.
        :param headers: Additional headers to include in the request.
        :param *args: Additional arguments to be passed to the underlying POST
               request.
        :param **kwargs: Additional keyword arguments to be passed to the
               underlying POST request.
        :return: requests.Response: The response object from the login request.
        """
        return await super().post(
            url,
            headers=headers,
            timeout=60,
            data=data,
        )

    async def login(self, url=None):
        """Attempt to log into the PACER site.
        The first step is to get an authentication token using a PACER
        username and password.
        To get the authentication token, it's necessary to send a POST request:
        curl --location --request POST 'https://pacer.login.uscourts.gov/services/cso-auth' \
            --header 'Accept: application/json' \
            --header 'User-Agent: Juriscraper' \
            --header 'Content-Type: application/json' \
            --data-raw '{
                "loginId": "USERNAME",
                "password": "PASSWORD"
            }'

        All documentation for PACER Authentication API User Guide can be found here:
        https://pacer.uscourts.gov/help/pacer/pacer-authentication-api-user-guide
        """
        logger.info("Attempting PACER API login")
        # Clear any remaining cookies. This is important because sometimes we
        # want to login before an old session has entirely died.
        self.cookies.clear()
        if url is None:
            url = self.LOGIN_URL
        # By default, it's assumed that the user is a filer. Redaction flag is set to 1
        data = {
            "loginId": self.username,
            "password": self.password,
            "redactFlag": "1",
        }
        # If optional client code information is included, include in login request
        if self.client_code:
            data["clientCode"] = self.client_code

        headers = {
            "User-Agent": self.user_agent,
            "Content-type": "application/json",
            "Accept": "application/json",
        }
        login_post_r = await self._prepare_login_request(
            url, data=json.dumps(data), headers=headers
        )

        if login_post_r.status_code != httpx.codes.OK:
            message = f"Unable connect to PACER site: '{login_post_r.status_code}: {login_post_r.reason_phrase}'"
            logger.warning(message)
            raise PacerLoginException(message)

        # Continue with login when response code is "200: OK"
        response_json = login_post_r.json()

        # 'loginResult': '0', user successfully logged; '1', user not logged
        if (
            response_json.get("loginResult") == None
            or response_json.get("loginResult") == "1"
        ):
            message = f"Invalid username/password: {response_json.get('errorDescription')}"
            raise PacerLoginException(message)
        # User logged, but with pending actions for their account
        if response_json.get("loginResult") == "0" and response_json.get(
            "errorDescription"
        ):
            logger.info(response_json.get("errorDescription"))

        if not response_json.get("nextGenCSO"):
            raise PacerLoginException(
                "Did not get NextGenCSO cookie when attempting PACER login."
            )
        # Set up cookie with 'nextGenCSO' token (128-byte string of characters)
        self.cookies.set(
            "NextGenCSO",
            response_json.get("nextGenCSO"),
            domain=".uscourts.gov",
            path="/",
        )
        # Support "CurrentGen" servers as well. This can be remoevd if they're
        # ever all upgraded to NextGen.
        self.cookies.set(
            "PacerSession",
            response_json.get("nextGenCSO"),
            domain=".uscourts.gov",
            path="/",
        )
        # If optional client code information is included,
        # 'PacerClientCode' cookie should be set
        if self.client_code:
            self.cookies.set(
                "PacerClientCode",
                self.client_code,
                domain=".uscourts.gov",
                path="/",
            )
        logger.info("New PACER session established.")

    def _do_additional_request(self, r: httpx.Response) -> bool:
        """Check if we should do an additional request to PACER, sometimes
        PACER returns the login page even though cookies are still valid.
        Do an additional GET request if we haven't done it previously.
        See https://github.com/freelawproject/courtlistener/issues/2160.

        :param r: The httpx Response object.
        :return: True if an additional request should be done, otherwise False.
        """
        if r.request.method == "GET" and self.additional_request_done is False:
            self.additional_request_done = True
            return True
        return False

    async def _login_again(self, r):
        """Log into PACER if the session has credentials and the session has
        expired.

        :param r: A response object to inspect for login errors.
        :returns: A boolean indicating whether a new session needed to be
        created.
        :raises: PacerLoginException, if unable to create a new session.
        """
        if is_pdf(r):
            return False

        if is_text(r):
            return False

        logged_in = check_if_logged_in_page(r.content)
        if logged_in:
            return False

        if self.username and self.password:
            logger.info(
                "Invalid/expired PACER session. Establishing new session."
            )
            await self.login()
            return True
        else:
            if self._do_additional_request(r):
                return True
            raise PacerLoginException(
                "Invalid/expired PACER session and do not have credentials "
                "for re-login."
            )
