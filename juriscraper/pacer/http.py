import gzip
import json
import re
from collections.abc import Iterator
from contextvars import ContextVar
from http.cookiejar import Cookie
from typing import Any

import httpx
from httpx import Cookies

from juriscraper.lib.exceptions import PacerLoginException
from juriscraper.lib.html_utils import (
    get_html_parsed_text,
    get_xml_parsed_text,
    strip_bad_html_tags_insecure,
)
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.pacer.utils import is_pdf, is_text

logger = make_default_logger()

# Compile the regex pattern once for efficiency.
# This pattern captures the court_id (e.g., 'ca9', 'ca2') from the URL.
ACMS_URL_PATTERN = re.compile(
    r"https?://(ca\d+)-showdoc(services)?\.azurewebsites\.us/.*"
)

# ACMS sets this cookie (plus chunked `...C1`, `...C2` variants) only after a
# successful SAML login. Azure's ARRAffinity cookies arrive on every response,
# so they can't tell a successful login from a rejected one.
ACMS_AUTH_COOKIE_PREFIX = ".AspNetCore.saml2"


def _iter_cookies(jar: Cookies) -> Iterator[Cookie]:
    """Iterate over the Cookie objects in a jar.

    HTTPX's Cookies wrapper iterates over names; its underlying jar yields
    Cookie objects.
    """
    return iter(jar.jar)


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
        # An unauthenticated PossibleCaseNumberApi XML result. Simply
        # continue onwards. The complete result looks like:
        # <request number='1501084'>
        #   <message text='Not logged in.  Please refresh this page.'/>
        # </request>
        # An authenticated PossibleCaseNumberApi XML result.
        return not not_logged_in

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
    return any(
        [
            found_district_logout_link,
            found_appellate_logout_link,
            is_a_download_confirmation_page,
            appellate_attachment_page,
            appellate_document_error,
        ]
    )


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
        get_acms_tokens=False,
        user_agent="Juriscraper",
        **kwargs,
    ):
        """
        Instantiate a new PACER API Session with some Juriscraper defaults
        :param cookies: an optional httpx.Cookies object with cookies for the session
        :param username: a PACER account username
        :param password: a PACER account password
        :param client_code: an optional PACER client code for the session
        :param get_acms_tokens: boolean flag to enable ACMS authentication during login.
        """
        self._anonymous_cookies: ContextVar[Cookies | None] = ContextVar(
            "pacer_anonymous_cookies", default=None
        )
        kwargs.setdefault("http2", True)
        kwargs.setdefault("follow_redirects", True)
        kwargs.setdefault("verify", False)
        super().__init__(**kwargs)
        self.user_agent = user_agent
        self.headers["User-Agent"] = self.user_agent
        self.headers["Referer"] = "https://external"  # For CVE-001-FLP.

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
        # Historical name. This now controls eager ACMS session initialization;
        # bearer tokens are fetched later during case requests.
        self.get_acms_tokens = get_acms_tokens
        self.acms_user_data = {}
        self.acms_tokens = {}
        # Per-court ACMS auth cookies
        self.acms_cookies: dict[str, Cookies] = {}

    @property
    def cookies(self) -> Cookies:
        cookies = self._anonymous_cookies.get()
        return super().cookies if cookies is None else cookies

    @cookies.setter
    def cookies(self, cookies) -> None:
        if self._anonymous_cookies.get() is None:
            httpx.AsyncClient.cookies.__set__(self, cookies)
        else:
            self._anonymous_cookies.set(Cookies(cookies))

    async def get_anonymous(
        self, url: str | httpx.URL, *, params=None, timeout=300
    ) -> httpx.Response:
        """GET without session headers, cookies, HTTP auth, or PACER login.

        Reuse this client's transport with fresh cookies for each call.
        Cookies set during redirects stay local to that call.
        """
        request = httpx.Request(
            "GET",
            url,
            params=params,
            extensions={"timeout": httpx.Timeout(timeout).as_dict()},
        )
        # HTTPX reads and updates self.cookies throughout the redirect chain.
        token = self._anonymous_cookies.set(Cookies())
        try:
            return await self.send(request, auth=httpx.Auth())
        finally:
            self._anonymous_cookies.reset(token)

    def _acms_court_for_url(self, url: str) -> str | None:
        """Return the ACMS court_id if `url` targets an ACMS host, else None."""
        match = ACMS_URL_PATTERN.match(url)
        return match.group(1) if match else None

    async def _ensure_acms_session(self, court_id: str) -> None:
        """
        Ensure an authenticated ACMS cookie session exists for the given court.

        Creates the session on first use and reuses it thereafter. This method
        establishes ACMS authentication cookies only.
        """
        if court_id not in self.acms_cookies:
            await self.establish_acms_session(court_id)

    def _acms_bearer_headers(self, court_id: str) -> dict[str, str]:
        """
        Return an Authorization header for the given ACMS court.

        Returns an empty dictionary when no bearer token has been established.
        """
        token = self.acms_tokens.get(court_id)
        if not token:
            return {}
        return {"Authorization": f"Bearer {token['Token']}"}

    async def _prepare_acms_request(
        self,
        url: str,
        kwargs: dict[str, Any],
    ) -> str | None:
        """
        Attach ACMS authentication state to the request.

        For ACMS endpoints, this method ensures a court-specific session
        exists and mutates ``kwargs`` in place to attach the appropriate
        cookies and authorization headers.

        Returns the court_id if the URL targets an ACMS endpoint,
        otherwise None.
        """
        court_id = self._acms_court_for_url(url)
        if not court_id:
            return None

        await self._ensure_acms_session(court_id)

        kwargs.setdefault("cookies", self.acms_cookies[court_id])

        bearer = self._acms_bearer_headers(court_id)
        if bearer:
            kwargs.setdefault("headers", {}).update(bearer)

        return court_id

    def _update_acms_cookies(self, court_id: str | None) -> None:
        """
        Move ACMS cookies set by the last request (including any redirects)
        into the court's jar.
        """
        if not court_id:
            return
        jar = self.acms_cookies[court_id]
        jar.update(self._take_acms_cookies())
        # clear Secure: the server re-issues cookies (e.g. Azure's
        # ARRAffinity) with Secure=True on most responses, which would
        # overwrite our desecured copies and break the webhook-sentry
        # https->http workaround.
        self._desecure_acms_cookies(jar)

    def store_acms_token(
        self, court_id: str, token: dict, user_data: dict | None = None
    ) -> None:
        """Persist a bearer token (and optional CsoId/ContactType) extracted
        from an IndexContent response, for reuse on showdocservices/api calls.

        :param court_id: ACMS court the token belongs to.
        :param token: the AuthToken object; must contain a "Token" key.
        :param user_data: optional {"CsoId", "ContactType"} for API bodies.
        """
        self.acms_tokens[court_id] = token
        if user_data:
            self.acms_user_data = user_data

    async def get(self, url, auto_login=True, **kwargs):
        """Overrides httpx.AsyncClient.get with session retry logic.

        For ACMS endpoints, this method automatically establishes and reuses
        court-specific authentication cookies. For PACER endpoints, it can
        transparently re-authenticate and retry requests when a session has
        expired.

        :param url: url string to GET
        :param auto_login: Whether the auto-login procedure should happen.
        :return: httpx.Response
        """
        court_id = await self._prepare_acms_request(url, kwargs)

        if "timeout" not in kwargs:
            kwargs.setdefault("timeout", 300)

        r = await super().get(url, **kwargs)
        self._update_acms_cookies(court_id)

        if b"This user has no access privileges defined." in r.content:
            # This is a strange error that we began seeing in CM/ECF 6.3.1 at
            # ILND. You can currently reproduce it by logging in on the central
            # login page, selecting "Court Links" as your destination, and then
            # loading: https://ecf.ilnd.uscourts.gov/cgi-bin/WrtOpRpt.pl
            # The solution when this error shows up is to simply re-run the get
            # request, so that's what we do here. PACER needs some frustrating
            # and inelegant hacks sometimes.
            r = await super().get(url, **kwargs)
        if auto_login and not court_id:
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

        For ACMS endpoints, this method automatically establishes and reuses
        court-specific authentication cookies. For PACER endpoints, it can
        transparently re-authenticate and retry requests when a session has
        expired.

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
        court_id = await self._prepare_acms_request(url, kwargs)

        kwargs.setdefault("timeout", 300)

        if data:
            pacer_data = self._prepare_multipart_form_data(data)
            kwargs.update({"files": pacer_data})
        else:
            kwargs.update({"data": data, "json": json})

        r = await super().post(url, **kwargs)
        self._update_acms_cookies(court_id)

        if auto_login and not court_id:
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
        output = {}
        for key in data:
            output[key] = (None, data[key])
        return output

    @staticmethod
    def _desecure_acms_cookies(jar: Cookies) -> None:
        """Clear Secure on ACMS cookies so webhook-sentry's https->http downgrade
        doesn't strip them. See freelawproject/courtlistener#5921."""
        for cookie in _iter_cookies(jar):
            cookie.secure = False

    def _take_acms_cookies(self) -> Cookies:
        """Move ACMS cookies out of the main PACER jar into a new jar.

        HTTPX stores every response's cookies (redirects included) in
        self.cookies. ACMS cookies are pulled out right away so they live only
        in the per-court jars and can't leak between courts.
        """
        jar = Cookies()
        # Copy to a list first: we remove cookies from the jar while iterating.
        for cookie in list(_iter_cookies(self.cookies)):
            if cookie.domain.endswith("azurewebsites.us"):
                jar.jar.set_cookie(cookie)
                self.cookies.delete(cookie.name, cookie.domain, cookie.path)
        return jar

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
        self, url, content=None, data=None, headers=None, *args, **kwargs
    ):
        """Prepares and sends a POST request for login purposes.

        This internal helper function constructs a POST request to the provided URL
        using the given headers and data. It sets a timeout of 60 seconds for the
        request.

        :param url: The URL of the login endpoint.
        :param content: A string containing login credentials.
        :param data: A dictionary containing login credentials.
        :param headers: Additional headers to include in the request.
        :param *args: Additional arguments to be passed to the underlying POST
               request.
        :param **kwargs: Additional keyword arguments to be passed to the
               underlying POST request.
        :return: httpx.Response: The response object from the login request.
        """
        return await super().post(
            url,
            content=content,
            data=data,
            headers=headers,
            timeout=60,
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
        # ACMS cookies are downstream of the PACER SAML assertion, so a fresh
        # PACER login invalidates them; drop them to force re-establishment on
        # the next ACMS request.
        self.acms_cookies = {}
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
            url, content=json.dumps(data), headers=headers
        )

        if login_post_r.status_code != httpx.codes.OK:
            message = f"Unable connect to PACER site: '{login_post_r.status_code}: {login_post_r.reason_phrase}'"
            logger.warning(message)
            raise PacerLoginException(message)

        # Continue with login when response code is "200: OK"
        response_json = login_post_r.json()

        # 'loginResult': '0', user successfully logged; '1', user not logged
        if (
            response_json.get("loginResult") is None
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
        session_cookies = Cookies()
        session_cookies.set(
            "NextGenCSO",
            response_json.get("nextGenCSO"),
            domain=".uscourts.gov",
            path="/",
        )
        # Support "CurrentGen" servers as well. This can be remoevd if they're
        # ever all upgraded to NextGen.
        session_cookies.set(
            "PacerSession",
            response_json.get("nextGenCSO"),
            domain=".uscourts.gov",
            path="/",
        )
        # If optional client code information is included,
        # 'PacerClientCode' cookie should be set
        if self.client_code:
            session_cookies.set(
                "PacerClientCode",
                self.client_code,
                domain=".uscourts.gov",
                path="/",
            )
        self.cookies = session_cookies
        logger.info("New PACER session established.")

        if self.get_acms_tokens:
            # Warm ACMS sessions for supported courts. Authentication tokens are
            # obtained later as part of the ACMS request flow and are not fetched
            # during session initialization.
            for court_id in ["ca2", "ca9"]:
                await self.establish_acms_session(court_id)

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

    def _get_docket_sheet_url(self, court_id: str) -> str:
        """
        Retrieves the base docket sheet URL for a given court ID. This URL
        serves as the initial entry point to trigger the authentication flow.

        :param court_id: The court identifier
        :return: The corresponding docket sheet URL.
        """
        if court_id == "ca9":
            return "https://ca9-showdoc.azurewebsites.us/"
        elif court_id == "ca2":
            return "https://ca2-showdoc.azurewebsites.us/"
        else:
            raise NotImplementedError(
                f"Docket sheet URL not implemented for court_id: {court_id}"
            )

    async def _get_saml_auth_request_parameters(
        self, court_id: str
    ) -> dict[str, str]:
        """
        Retrieves SAML authentication request parameters by initiating a request
        to the DOCKET_SHEET_URL. This simulates the initial browser interaction
        that triggers the SAML flow, parsing hidden input fields from the
        response.

        :param court_id: The court identifier.
        :return: A dictionary where keys are the 'name' attributes and values are
            the 'value' attributes of hidden input elements found in the SAML
            authentication request form.
        """
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
        }
        logger.info(f"Attempting to get SAML credentials for {court_id}")
        # Base URL for retrieving SAML credentials.
        url = self._get_docket_sheet_url(court_id)
        response = await self._prepare_login_request(
            url, data={}, headers=headers
        )
        result_parts = response.text.split("\r\n")
        # Handle gzip decoding
        js_screen = result_parts[-1]
        try:
            # Try to decompress if it's gzipped
            inflated_screen = gzip.decompress(js_screen.encode()).decode()
        except Exception:
            # If decompression fails, use the original
            inflated_screen = js_screen

        # Strip potentially problematic HTML tags for safer parsing.
        html = strip_bad_html_tags_insecure(inflated_screen)
        # Extract all hidden input elements from the HTML.
        hidden_inputs = html.xpath('//input[@type="hidden"]')

        # Return a dictionary of hidden input names and their values.
        return {
            input_element.get("name"): input_element.get("value")
            for input_element in hidden_inputs
        }

    async def establish_acms_session(self, court_id: str) -> None:
        """Establish ACMS auth cookies for `court_id` via the SAML flow.

        The handshake runs on this session through ``_prepare_login_request``
        The resulting ACMS cookies are moved into ``self.acms_cookies[court_id]``.

        Requires:
            ``login()`` has already been called and ``self.cookies`` contains a
            valid PACER session.
        """
        if not self.cookies:
            raise PacerLoginException(
                "Cannot establish an ACMS session before login(): no PACER cookies."
            )

        # Discard leftover ACMS cookies so they don't end up in this court's jar.
        self._take_acms_cookies()

        auth_params = await self._get_saml_auth_request_parameters(court_id)
        # An expired PACER session lands on PACER's login form instead of the
        # SAML form. Its hidden inputs would pass a plain emptiness check.
        if not auth_params.get("SAMLResponse"):
            raise PacerLoginException(
                f"No SAMLResponse for {court_id}. The PACER session is "
                "probably invalid."
            )

        logger.info(f"Establishing ACMS session for {court_id}")
        saml_url = f"https://{court_id}-showdoc.azurewebsites.us/Saml2/Acs"
        response = await self._prepare_login_request(
            saml_url,
            data=auth_params,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()

        # Keep a separate ACMS cookie jar per court so that broadly scoped
        # cookies from one court cannot override another court's session state.
        acms_jar = self._take_acms_cookies()
        # A rejected login still answers 200 (ACMS redirects to its own login
        # page) and still carries Azure's affinity cookies, so check for the
        # auth cookie itself.
        if not any(
            c.name.startswith(ACMS_AUTH_COOKIE_PREFIX)
            for c in _iter_cookies(acms_jar)
        ):
            raise PacerLoginException(
                f"ACMS rejected the SAML login for {court_id}."
            )
        self._desecure_acms_cookies(acms_jar)
        self.acms_cookies[court_id] = acms_jar
        logger.info(f"ACMS session established for {court_id}")

    # Kept so existing callers don't break on the old name. Unlike the old
    # method, this no longer sets acms_tokens or acms_user_data: ACMS doesn't
    # return them in the SAML response anymore. They're populated via
    # store_acms_token() from IndexContent responses instead.
    get_acms_auth_object = establish_acms_session
