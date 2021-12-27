import json
import re

import requests
from requests.packages.urllib3 import exceptions

from ..lib.exceptions import PacerLoginException
from ..lib.html_utils import get_html_parsed_text, get_xml_parsed_text
from ..lib.log_tools import make_default_logger
from ..pacer.utils import is_pdf, is_text

logger = make_default_logger()

requests.packages.urllib3.disable_warnings(exceptions.InsecureRequestWarning)


def check_if_logged_in_page(text):
    """Is this a valid HTML page from PACER?

    Check if the html in 'text' is from a valid PACER page or valid PACER XML
    document, or if it's from a page telling you to log in or informing you
    that you're not logged in.
    :param text: The HTML or XML of the page to test
    :return boolean: True if logged in, False if not.
    """
    if isinstance(text, bytes):
        text = text.decode("utf-8")

    valid_case_number_query = (
        "<case number=" in text
        or "<request number=" in text
        or 'id="caseid"' in text
        or "Cost: " in text
    )
    no_results_case_number_query = re.search("<message.*Cannot find", text)
    sealed_case_query = re.search("<message.*Case Under Seal", text)
    if any(
        [
            valid_case_number_query,
            no_results_case_number_query,
            sealed_case_query,
        ]
    ):
        not_logged_in = re.search("text.*Not logged in", text)
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
    found_district_logout_link = "/cgi-bin/login.pl?logout" in text
    found_appellate_logout_link = "InvalidUserLogin.jsp" in text
    if any([found_district_logout_link, found_appellate_logout_link]):
        # A normal HTML page we're logged into.
        return True

    return False


class PacerSession(requests.Session):
    """
    Extension of requests.Session to handle PACER oddities making it easier
    for folks to just POST data to PACER endpoints/apis.

    Also includes utilities for logging into PACER and re-logging in when
    sessions expire.
    """

    LOGIN_URL = "https://pacer.login.uscourts.gov/services/cso-auth"

    def __init__(
        self, cookies=None, username=None, password=None, client_code=None
    ):
        """
        Instantiate a new PACER API Session with some Juriscraper defaults
        :param cookies: an optional RequestsCookieJar object with cookies for the session
        :param username: a PACER account username
        :param password: a PACER account password
        :param client_code: an optional PACER client code for the session
        """
        super().__init__()
        self.headers["User-Agent"] = "Juriscraper"
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

    def get(self, url, auto_login=True, **kwargs):
        """Overrides request.Session.get with session retry logic.

        :param url: url string to GET
        :param auto_login: Whether the auto-login procedure should happen.
        :return: requests.Response
        """
        kwargs.setdefault("timeout", 300)

        r = super().get(url, **kwargs)

        if "This user has no access privileges defined." in r.text:
            # This is a strange error that we began seeing in CM/ECF 6.3.1 at
            # ILND. You can currently reproduce it by logging in on the central
            # login page, selecting "Court Links" as your destination, and then
            # loading: https://ecf.ilnd.uscourts.gov/cgi-bin/WrtOpRpt.pl
            # The solution when this error shows up is to simply re-run the get
            # request, so that's what we do here. PACER needs some frustrating
            # and inelegant hacks sometimes.
            r = super().get(url, **kwargs)
        if auto_login:
            updated = self._login_again(r)
            if updated:
                # Re-do the request with the new session.
                return super().get(url, **kwargs)
        return r

    def post(self, url, data=None, json=None, auto_login=True, **kwargs):
        """
        Overrides requests.Session.post with PACER-specific fun.

        Will automatically convert data dict into proper multi-part form data
        and pass to the files parameter instead.

        Will set a timeout of 300 if not provided.

        All other uses or parameters will pass through untouched
        :param url: url string to post to
        :param data: post data
        :param json: json object to post
        :param auto_login: Whether the auto-login procedure should happen.
        :param kwargs: assorted keyword arguments
        :return: requests.Response
        """
        kwargs.setdefault("timeout", 300)

        if data:
            pacer_data = self._prepare_multipart_form_data(data)
            kwargs.update({"files": pacer_data})
        else:
            kwargs.update({"data": data, "json": json})

        r = super().post(url, **kwargs)
        if auto_login:
            updated = self._login_again(r)
            if updated:
                # Re-do the request with the new session.
                return super().post(url, **kwargs)
        return r

    def head(self, url, **kwargs):
        """
        Overrides request.Session.head with a default timeout parameter.

        :param url: url string upon which to do a HEAD request
        :param kwargs: assorted keyword arguments
        :return: requests.Response
        """
        kwargs.setdefault("timeout", 300)
        return super().head(url, **kwargs)

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

        :param r: A request.Response object
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

    def login(self, url=None):
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

        login_post_r = super().post(
            url,
            headers={
                "User-Agent": "Juriscraper",
                "Content-type": "application/json",
                "Accept": "application/json",
            },
            timeout=60,
            data=json.dumps(data),
        )

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
        session_cookies = requests.cookies.RequestsCookieJar()
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

    def _login_again(self, r):
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

        logged_in = check_if_logged_in_page(r.text)
        if logged_in:
            return False

        if self.username and self.password:
            logger.info(
                "Invalid/expired PACER session. Establishing new session."
            )
            self.login()
            return True
        else:
            raise PacerLoginException(
                "Invalid/expired PACER session and do not have credentials "
                "for re-login."
            )
