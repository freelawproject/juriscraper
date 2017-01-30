"""
Functions for Authenticating with PACER
"""
import re
import requests

from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger()


class PacerSession(requests.Session):
    """
    Extension of requests.Session to handle PACER oddities making it easier
    for folks to just POST data to PACER endpoints/apis
    """

    def __init__(self, pacer_token=None):
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
        if kwargs:
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 300
        else:
            kwargs = {'timeout': 300}

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
        return 'https://dcecf.psc.uscourts.gov/cgi-bin/login.pl'
    else:
        return 'https://ecf.%s.uscourts.gov/cgi-bin/login.pl' % court_id


def login(court_id, username, password):
    """
    Log into a PACER jurisdiction
    :param court_id: id of the court to authenticate with
    :param username: PACER username
    :param password: PACER password
    :return: new PacerSession configured with PacerSession token in cookie
    """
    url = _make_login_url(court_id)
    logger.info("Logging into: %s at %s" % (court_id, url))
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
        raise BadLoginException(r.text)

    # The cookie value is in the HTML. Extract it.
    m = re.search('PacerSession=(\w+);', r.text)
    if m is not None:
        return PacerSession(pacer_token=m.group(1))

    raise BadLoginException('could not create new PacerSession')


class BadLoginException(Exception):
    """Raised when the system cannot authenticate with PACER"""

    def __init__(self, message):
        Exception.__init__(self, message)