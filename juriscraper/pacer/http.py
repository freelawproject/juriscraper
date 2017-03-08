"""
Functions for Authenticating with PACER
"""
import re
import requests

from juriscraper.lib.log_tools import make_default_logger
from requests.packages.urllib3 import exceptions

logger = make_default_logger()

requests.packages.urllib3.disable_warnings(exceptions.InsecureRequestWarning)


class PacerSession(requests.Session):
    """
    Extension of requests.Session to handle PACER oddities making it easier
    for folks to just POST data to PACER endpoints/apis
    """

    def __init__(self, pacer_token=None, cookie_jar=None):
        """
        Instantiate a new PACER HTTP Session with some Juriscraper defaults
        :param pacer_token: a PACER_SESSION token value
        """
        super(PacerSession, self).__init__()
        self.headers['User-Agent'] = 'Juriscraper'
        self.verify = False

        if pacer_token:
            self.cookies.set('PacerSession',
                             pacer_token,
                             domain='.uscourts.gov',
                             path='/')

        if cookie_jar:
            self.cookies = cookie_jar

    def post(self, url, data=None, json=None, **kwargs):
        """
        Overrides requests.Session.post with PACER-specific fun.

        Will automatically convert data dict into proper multi-part form data
        and pass to the files parameter instead.

        Will set a timeout of 300 if not provided.

        All other uses or parameters will pass through untouched
        :param url: url string to post to
        :param data: post data
        :param json: json object to post
        :param kwargs: assorted keyword arguments
        :return: requests.Response
        """
        kwargs.setdefault('timeout', 300)

        if data:
            pacer_data = self._prepare_multipart_form_data(data)
            return super(PacerSession, self).post(url, files=pacer_data, **kwargs)

        return super(PacerSession, self).post(url, data=data, json=json, **kwargs)

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


def _make_login_url(court_id):
    """Make a login URL for a given court id."""
    if court_id == 'psc':
        # training account
        return 'https://dcecf.psc.uscourts.gov/cgi-bin/login.pl'
    return 'https://pacer.login.uscourts.gov/csologin/login.jsf?pscCourtId=%s' % court_id


def login(court_id, username, password):
    """
    Log into a PACER jurisdiction via the main PACER portal which should set our global PacerSession

    :param court_id: id of the court to authenticate with
    :param username: PACER username
    :param password: PACER password
    :return: new PacerSession configured with PacerSession token in cookie
    """
    if court_id == 'psc':
        return _login_training(court_id, username, password)

    url = _make_login_url(court_id)
    logger.info("Logging into: %s at %s" % (court_id, url))

    login_session = requests.Session()
    login_session.headers['User-Agent'] = 'Juriscraper'
    login_session.verify = False

    # initial GET to login page to get JSESSIONID
    r = login_session.get(url, timeout=60)
    if not r.status_code == 200:
        msg = 'Could not navigate to PACER central login url: %s' % url
        logger.error(msg)
        raise PacerLoginException(msg)

    # with our JSESSIONID, try the login
    login_data = {
        'login': 'login',
        'login:loginName': username,
        'login:password': password,
        'login:clientCode': '',
        'login:fbtnLogin': '',
        'javax.faces.ViewState': 'stateless'
    }
    r = login_session.post(url, timeout=60, data=login_data, allow_redirects=False)

    if r.status_code == 302:
        # we should be redirected on success with cookies!
        if not login_session.cookies.get('PacerSession', None, '.uscourts.gov', '/'):
            logger.error('Failed to get a PacerSession token!')
            raise PacerLoginException('Failed to get a PacerSession token!')
    else:
        msg = 'Unknown PACER login error: http status %s' % r.status_code
        if 'Invalid ID or password' in r.text:
            msg = 'Invalid PACER ID or password.'
        logger.error(msg)
        raise PacerLoginException(msg)

    logger.info('New PacerSession established.')
    return PacerSession(cookie_jar=login_session.cookies)


def _login_training(court_id, username, password):
    """
    Attempt to log into the PACER training site.
    :param court_id: training court_id
    :param username: training username
    :param password: training password
    :return:
    """
    url = _make_login_url(court_id)
    logger.info('attempting PACER Training Site login')
    r = requests.post(
        url,
        headers={'User-Agent': 'Juriscraper'},
        verify=False,
        timeout=60,
        data={
            'login': username,
            'key': password
        },
    )
    if 'Invalid ID or password' in r.text:
        raise BadPacerCredentials(r.text)

    # The cookie value is in the HTML. Extract it.
    m = re.search('PacerSession=(\w+);', r.text)
    if m is not None:
        return PacerSession(pacer_token=m.group(1))

    raise PacerLoginException('could not create new training PacerSession')


class PacerLoginException(Exception):
    """Raised when the system cannot authenticate with PACER"""

    def __init__(self, message):
        Exception.__init__(self, message)


class BadPacerCredentials(Exception):
    """Raised when the credentials failed to authenticate the client to PACER"""

    def __init__(self, message):
        Exception.__init__(self, message)
