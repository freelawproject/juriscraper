"""
Functions for Authenticating with PACER
"""
import re
import requests
from requests import Session
from requests.cookies import RequestsCookieJar

from juriscraper.lib.log_tools import make_default_logger

from .exceptions import BadLoginException

logger = make_default_logger()


class PacerSession(Session):
    """
    PACER-specific Requests Session object for handling the lovely non-standard
    HTTP implementation at PACER
    :param Session: requests.Session
    :return: new PACER Session
    """

    def __init__(self, pacer_session=None):
        super(PacerSession, self).__init__()
        self.headers['User-Agent'] = 'Juriscraper'
        self.verify = False

        if pacer_session:
            self.cookies.set('PacerSession',
                             pacer_session,
                             domain='.uscourts.gov',
                             path='/')

    def post(self, url, data=None, json=None, **kwargs):
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
    """Log into a PACER jurisdiction. Return a new PacerSession"""
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
        return PacerSession(pacer_session=m.group(1))

    raise BadLoginException('could not create new PacerSession')
