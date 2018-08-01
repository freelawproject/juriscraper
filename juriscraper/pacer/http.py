import re

import requests
from requests.packages.urllib3 import exceptions

from ..lib.exceptions import PacerLoginException
from ..lib.log_tools import make_default_logger
from ..pacer.utils import is_pdf

logger = make_default_logger()

requests.packages.urllib3.disable_warnings(exceptions.InsecureRequestWarning)


class PacerSession(requests.Session):
    """
    Extension of requests.Session to handle PACER oddities making it easier
    for folks to just POST data to PACER endpoints/apis.

    Also includes utilities for logging into PACER and re-logging in when
    sessions expire.
    """
    LOGIN_URL = 'https://pacer.login.uscourts.gov/csologin/login.jsf'

    def __init__(self, cookies=None, username=None, password=None):
        """
        Instantiate a new PACER HTTP Session with some Juriscraper defaults
        :param pacer_token: a PACER_SESSION token value
        """
        super(PacerSession, self).__init__()
        self.headers['User-Agent'] = 'Juriscraper'
        self.headers['Referer'] = 'https://external'  # For CVE-001-FLP.
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
        kwargs.setdefault('timeout', 300)

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
        kwargs.setdefault('timeout', 300)

        if data:
            pacer_data = self._prepare_multipart_form_data(data)
            kwargs.update({'files': pacer_data})
        else:
            kwargs.update({'data': data, 'json': json})

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
        kwargs.setdefault('timeout', 300)
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

    def login(self, url=None):
        """Attempt to log into the PACER site.

        Logging into PACER has two flows. If you have filing permission in any
        court, you wind up making three POST request which are tied together by
        a JSESSIONID value that's in a cookie set by the first request.

        If you do *not* have filing permissions, only the first request below
        is needed. The trick to determine what's needed is to watch for a 302
        response status or the cookies to be set properly. If you get one or
        the other, that indicates that you're logged in or that you're being
        redirected to the correct court/webpage.

        Here are the requests that are needed. First, submit your user/pass:

            curl 'https://pacer.login.uscourts.gov/csologin/login.jsf' \
              -H 'Content-Type: application/x-www-form-urlencoded' \
              --data 'login=login&login%3AloginName=mlissner.flp&login%3Apassword=QKAXmos0DyAtpX%26U30O7Vqt%401NNwa3z%5E&login%3AclientCode=&login%3AfbtnLogin=&javax.faces.ViewState=stateless' \
              --verbose > /tmp/curl-out.html

        If this is *not* a filing account, you should receive a 302 response
        and the proper cookies at this point. You're logged in.

        If this *is* a filing account, the second request happens when you
        click the *box* (not the button) saying you'll agree to the redaction
        rules. Note that the JSESSIONID cookie in this request and the next one
        is set by the previous request and needs to be carried through. If you
        receive a new JSESSIONID cookie in response to your second request,
        something has gone wrong:

            curl 'https://pacer.login.uscourts.gov/csologin/login.jsf' \
              -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
              -H 'Cookie: JSESSIONID=C73BDC1E4CA8C5BDEE13EB2F4CB75E06' \
              --data 'javax.faces.partial.ajax=true&javax.faces.source=regmsg%3AchkRedact&javax.faces.partial.execute=regmsg%3AchkRedact&javax.faces.partial.render=regmsg%3AbpmConfirm&javax.faces.behavior.event=valueChange&javax.faces.partial.event=change&regmsg=regmsg&regmsg%3AchkRedact_input=on&javax.faces.ViewState=stateless' \
              --verbose > /tmp/curl-out.html

        The third request happens when you submit the form saying you promise
        to redact:

            curl 'https://pacer.login.uscourts.gov/csologin/login.jsf' \
              -H 'Content-Type: application/x-www-form-urlencoded' \
              -H 'Cookie: JSESSIONID=C73BDC1E4CA8C5BDEE13EB2F4CB75E06' \
              --data 'regmsg=regmsg&regmsg%3AchkRedact_input=on&regmsg%3AbpmConfirm=&javax.faces.ViewState=stateless'\
              --verbose > /tmp/curl-out.html

        If you get a 302 response and the proper cookies at this point, that
        means you're logged in.
        """
        logger.info(u'Attempting PACER site login')
        if url is None:
            url = self.LOGIN_URL
        r = self.post(
            url,
            headers={'User-Agent': 'Juriscraper'},
            verify=False,
            timeout=60,
            auto_login=False,
            data={
                'javax.faces.ViewState': 'stateless',
                'login': 'login',
                'login:clientCode': '',
                'login:fbtnLogin': '',
                'login:loginName': self.username,
                'login:password': self.password,
            },
        )
        if u'Invalid username or password' in r.text:
            raise PacerLoginException("Invalid username/password")
        if u'Username must be at least 6 characters' in r.text:
            raise PacerLoginException("Username must be at least six "
                                      "characters")
        if u'Password must be at least 8 characters' in r.text:
            raise PacerLoginException("Password must be at least eight "
                                      "characters")
        if u'timeout error' in r.text:
            raise PacerLoginException("Timeout")

        if not self.cookies.get('PacerSession'):
            logger.info("Did not get cookies from first log in POST. Assuming "
                        "this is a filing user and doing two more POSTs.")
            self.post(
                url,
                headers={'User-Agent': 'Juriscraper'},
                verify=False,
                timeout=60,
                auto_login=False,
                data={
                    'javax.faces.partial.ajax': 'true',
                    'javax.faces.source': 'regmsg:chkRedact',
                    'javax.faces.partial.execute': 'regmsg:chkRedact',
                    'javax.faces.partial.render': 'regmsg:bpmConfirm',
                    'javax.faces.behavior.event': 'valueChange',
                    'javax.faces.partial.event': 'change',
                    'regmsg': 'regmsg',
                    'regmsg:chkRedact_input': 'on',
                    'javax.faces.ViewState': 'stateless',
                },
            )
            # The box is now checked. Submit the form to say so.
            self.post(
                url,
                headers={'User-Agent': 'Juriscraper'},
                verify=False,
                timeout=60,
                auto_login=False,
                data={
                    'regmsg': 'regmsg',
                    'regmsg:chkRedact_input': 'on',
                    'regmsg:bpmConfirm': '',
                    'javax.faces.ViewState': 'stateless',
                },
            )

        if not self.cookies.get('PacerSession') and \
                not self.cookies.get('NextGenCSO'):
            raise PacerLoginException(
                'Did not get PacerSession and NextGenCSO '
                'cookies when attempting PACER login.'
            )

        logger.info(u'New PACER session established.')

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

        valid_case_number_query = '<case number=' in r.text or \
            "<request number=" in r.text
        no_results_case_number_query = re.search('<message.*Cannot find', r.text)
        sealed_case_query = re.search('<message.*Case Under Seal', r.text)
        if any([valid_case_number_query, no_results_case_number_query,
                sealed_case_query]):
            # An authenticated PossibleCaseNumberApi XML result.
            return False

        found_district_logout_link = '/cgi-bin/login.pl?logout' in r.text
        found_appellate_logout_link = 'InvalidUserLogin.jsp' in r.text
        if any([found_district_logout_link, found_appellate_logout_link]):
            # A normal HTML page we're logged into.
            return False

        if self.username and self.password:
            logger.info(u"Invalid/expired PACER session. Establishing new "
                        u"session.")
            self.login()
            return True
        else:
            msg = (u"Invalid/expired PACER session and do not have credentials "
                   u"for re-login.")
            logger.error(msg)
            raise PacerLoginException(msg)
