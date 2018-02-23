import re

import requests
from requests.packages.urllib3 import exceptions

from ..lib.exceptions import PacerLoginException
from ..lib.log_tools import make_default_logger
from ..pacer.utils import is_pdf, get_court_id_from_url

logger = make_default_logger()

requests.packages.urllib3.disable_warnings(exceptions.InsecureRequestWarning)


class PacerSession(requests.Session):
    """
    Extension of requests.Session to handle PACER oddities making it easier
    for folks to just POST data to PACER endpoints/apis.

    Also includes utilities for logging into PACER and re-logging in when
    sessions expire.
    """
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
        """Attempt to log into the PACER site."""
        if url is None:
            url = self._make_login_url()
        logger.info(u'Attempting PACER site login')
        r = self.post(
            url,
            headers={'User-Agent': 'Juriscraper'},
            verify=False,
            timeout=60,
            auto_login=False,
            data={
                'login': self.username,
                'key': self.password,
            },
        )
        if u'Invalid ID or password' in r.text:
            raise PacerLoginException("Invalid username/password")
        if u'timeout error' in r.text:
            raise PacerLoginException("Timeout")
        # The cookie value is in the HTML. Extract it.
        m = re.search('PacerSession=(\w+);', r.text)
        if m is not None:
            self.cookies.set('PacerSession', m.group(1), domain='.uscourts.gov',
                             path='/')
        else:
            raise PacerLoginException('Could not log into PACER')

        logger.info(u'New PACER session established.')

    def login_training(self):
        url = self._make_login_url('psc')
        self.login(url=url)

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

        valid_case_number_query = '<case number=' in r.text
        no_results_case_number_query = re.search('<message.*Cannot find', r.text)
        sealed_case_query = re.search('<message.*Case Under Seal', r.text)
        if any([valid_case_number_query, no_results_case_number_query,
                sealed_case_query]):
            # An authenticated PossibleCaseNumberApi XML result.
            return False

        if '/cgi-bin/login.pl?logout' in r.text:
            # A normal HTML page we're logged into.
            return False

        if self.username and self.password:
            logger.info(u"Invalid/expired PACER session. Establishing new "
                        u"session.")
            court_id = get_court_id_from_url(r.url)
            if court_id == 'psc':
                self.login_training()
            else:
                self.login()
            return True
        else:
            msg = (u"Invalid/expired PACER session and do not have credentials "
                   u"for re-login.")
            logger.error(msg)
            raise PacerLoginException(msg)

    @staticmethod
    def _make_login_url(court_id=None):
        """Make a login URL for a given court id."""
        if court_id == 'psc':
            # training website
            return 'https://dcecf.psc.uscourts.gov/cgi-bin/login.pl'
        return 'https://ecf.cand.uscourts.gov/cgi-bin/login.pl'
