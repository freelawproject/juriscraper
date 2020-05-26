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

    LOGIN_URL = "https://pacer.login.uscourts.gov/csologin/login.jsf"
    INDEX = "https://ecf.ilnd.uscourts.gov/cgi-bin/ShowIndex.pl"

    def __init__(self, cookies=None, username=None, password=None):
        """
        Instantiate a new PACER HTTP Session with some Juriscraper defaults
        :param pacer_token: a PACER_SESSION token value
        """
        super(PacerSession, self).__init__()
        self.headers["User-Agent"] = "Juriscraper"
        self.headers["Referer"] = "https://external"  # For CVE-001-FLP.
        self.verify = False

        if cookies:
            self.cookies = cookies

        self.username = username
        self.password = password

    def get(self, url, auto_login=True, **kwargs):
        """Overrides request.Session.get with session retry logic.

        :param url: url string to GET
        :param auto_login: Whether the auto-login procedure should happen.
        :return: requests.Response
        """
        kwargs.setdefault("timeout", 300)

        r = super(PacerSession, self).get(url, **kwargs)

        if "This user has no access privileges defined." in r.text:
            # This is a strange error that we began seeing in CM/ECF 6.3.1 at
            # ILND. You can currently reproduce it by logging in on the central
            # login page, selecting "Court Links" as your destination, and then
            # loading: https://ecf.ilnd.uscourts.gov/cgi-bin/WrtOpRpt.pl
            # The solution when this error shows up is to simply re-run the get
            # request, so that's what we do here. PACER needs some frustrating
            # and inelegant hacks sometimes.
            r = super(PacerSession, self).get(url, **kwargs)
        if auto_login:
            updated = self._login_again(r)
            if updated:
                # Re-do the request with the new session.
                return super(PacerSession, self).get(url, **kwargs)
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

        r = super(PacerSession, self).post(url, **kwargs)
        if auto_login:
            updated = self._login_again(r)
            if updated:
                # Re-do the request with the new session.
                return super(PacerSession, self).post(url, **kwargs)
        return r

    def head(self, url, **kwargs):
        """
        Overrides request.Session.head with a default timeout parameter.

        :param url: url string upon which to do a HEAD request
        :param kwargs: assorted keyword arguments
        :return: requests.Response
        """
        kwargs.setdefault("timeout", 300)
        return super(PacerSession, self).head(url, **kwargs)

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

        Logging into PACER has two flows. If you have filing permission in any
        court, you wind up making four POST request which are tied together by
        a JSESSIONID cookie value and ViewState hidden form inputs.

        If you do *not* have filing permissions, only the first request below
        is needed. The trick to determine what's needed is to watch for a 302
        response status or the cookies to be set properly. If you get one or
        the other, that indicates that you're logged in or that you're being
        redirected to the correct court/webpage.

        Here are the requests that are needed. First, just GET the login page
        and parse out the ViewState form value. Then, submit your user/pass:

            curl 'https://pacer.login.uscourts.gov/csologin/login.jsf' \
              -H 'Content-Type: application/x-www-form-urlencoded' \
              --data 'login=login&login%3AloginName=mlissner.flp&login%3Apassword=QKAXmos0DyAtpX%26U30O7Vqt%401NNwa3z%5E&login%3AclientCode=&login%3AfbtnLogin=&javax.faces.ViewState=stateless' \
              --verbose > /tmp/curl-out.html

        If this is *not* a filing account, you should receive a 302 response
        and the proper cookies at this point. You're logged in.

        If this *is* a filing account, the third request happens when you
        click the *box* (not the button) saying you'll agree to the redaction
        rules. Note that the JSESSIONID cookie in this request and the next one
        is set by the previous request and needs to be carried through. If you
        receive a new JSESSIONID cookie in response to your second request,
        something has gone wrong. We also grab the ViewState value from the
        previous request:

            curl 'https://pacer.login.uscourts.gov/csologin/login.jsf' \
              -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
              -H 'Cookie: JSESSIONID=C73BDC1E4CA8C5BDEE13EB2F4CB75E06' \
              --data 'javax.faces.partial.ajax=true&javax.faces.source=regmsg%3AchkRedact&javax.faces.partial.execute=regmsg%3AchkRedact&javax.faces.partial.render=regmsg%3AbpmConfirm&javax.faces.behavior.event=valueChange&javax.faces.partial.event=change&regmsg=regmsg&regmsg%3AchkRedact_input=on&javax.faces.ViewState=stateless' \
              --verbose > /tmp/curl-out.html

        The fourth request happens when you submit the form saying you promise
        to redact:

            curl 'https://pacer.login.uscourts.gov/csologin/login.jsf' \
              -H 'Content-Type: application/x-www-form-urlencoded' \
              -H 'Cookie: JSESSIONID=C73BDC1E4CA8C5BDEE13EB2F4CB75E06' \
              --data 'regmsg=regmsg&regmsg%3AchkRedact_input=on&regmsg%3AbpmConfirm=&javax.faces.ViewState=stateless'\
              --verbose > /tmp/curl-out.html

        If you get a 302 response and the proper cookies at this point, that
        means you're logged in.
        """
        logger.info(u"Attempting PACER site login")

        # Clear any remaining cookies. This is important because sometimes we
        # want to login before an old session has entirely died. One example of
        # when we do that is when we get the page saying that "This page will
        # expire in...[so many minutes]." When we see that we just log in
        # fresh and try again.
        self.cookies.clear()
        if url is None:
            url = self.LOGIN_URL

        # Load the page in order to get the ViewState value from the HTML
        load_page_r = self.get(
            url,
            headers={"User-Agent": "Juriscraper"},
            auto_login=False,
            verify=False,
            timeout=60,
        )

        login_post_r = self.post(
            url,
            headers={"User-Agent": "Juriscraper"},
            verify=False,
            timeout=60,
            auto_login=False,
            data={
                "javax.faces.partial.ajax": "true",
                "javax.faces.partial.execute": "@all",
                "javax.faces.source": "loginForm:fbtnLogin",
                "javax.faces.partial.render": "pscLoginPanel+loginForm+redactionConfirmation+popupMsgId",
                "javax.faces.ViewState": self._get_view_state(load_page_r),
                "loginForm:courtId_input": "E_ALMDC",
                "loginForm:courtId_focus": "",
                "loginForm:fbtnLogin": "loginForm:fbtnLogin",
                "loginForm:loginName": self.username,
                "loginForm:password": self.password,
                "loginForm:clientCode": "",
                "loginForm": "loginForm",
            },
        )
        if u"Invalid username or password" in login_post_r.text:
            raise PacerLoginException("Invalid username/password")
        if u"Username must be at least 6 characters" in login_post_r.text:
            raise PacerLoginException(
                "Username must be at least six " "characters"
            )
        if u"Password must be at least 8 characters" in login_post_r.text:
            raise PacerLoginException(
                "Password must be at least eight " "characters"
            )
        if u"timeout error" in login_post_r.text:
            raise PacerLoginException("Timeout")

        if not self.cookies.get("PacerSession"):
            logger.info(
                "Did not get cookies from first log in POSTs. "
                "Assuming this is a filing user and doing two more "
                "POSTs."
            )
            reg_msg_r = self.post(
                url,
                headers={"User-Agent": "Juriscraper"},
                verify=False,
                timeout=60,
                auto_login=False,
                data={
                    "javax.faces.partial.ajax": "true",
                    "javax.faces.source": "regmsg:chkRedact",
                    "javax.faces.partial.execute": "regmsg:chkRedact",
                    "javax.faces.partial.render": "regmsg:bpmConfirm",
                    "javax.faces.partial.event": "change",
                    "javax.faces.behavior.event": "valueChange",
                    "javax.faces.ViewState": self._get_xml_view_state(
                        login_post_r
                    ),
                    "regmsg": "regmsg",
                    "regmsg:chkRedact_input": "on",
                },
            )
            # The box is now checked. Submit the form to say so.
            self.post(
                url,
                headers={"User-Agent": "Juriscraper"},
                verify=False,
                timeout=60,
                auto_login=False,
                data={
                    "javax.faces.partial.ajax": "true",
                    "javax.faces.source": "regmsg:bpmConfirm",
                    "javax.faces.partial.execute": "@all",
                    "javax.faces.ViewState": self._get_xml_view_state(
                        reg_msg_r
                    ),
                    "regmsg": "regmsg",
                    "regmsg:chkRedact_input": "on",
                    "regmsg:bpmConfirm": "regmsg:bpmConfirm",
                    "dialogName": "redactionDlg",
                },
            )

        if not self.cookies.get("PacerSession") and not self.cookies.get(
            "NextGenCSO"
        ):
            raise PacerLoginException(
                "Did not get PacerSession and NextGenCSO "
                "cookies when attempting PACER login."
            )

        self.get(self.INDEX, auto_login=False)
        logger.info(u"New PACER session established.")

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
                u"Invalid/expired PACER session. Establishing new " u"session."
            )
            self.login()
            return True
        else:
            msg = (
                u"Invalid/expired PACER session and do not have "
                u"credentials for re-login."
            )
            logger.error(msg)
            raise PacerLoginException(msg)
