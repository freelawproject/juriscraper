import re

import requests

from exceptions import BadLoginException
from juriscraper.pacer.free_documents import logger


def make_pacer_cookie_dict(name, value):
    """Make a cookie dict with the provided name and value"""
    return {
        "version": 0,
        'name': name,
        'value': value,
        'port': None,
        'domain': '.uscourts.gov',
        'path': '/',
        'secure': True,
        'rest': {
            'hostonly': False,
            'httponly': False,
        }
    }


def make_login_url(court_id):
    """Make a login URL for a given court id."""
    if court_id == 'psc':
        return 'https://dcecf.psc.uscourts.gov/cgi-bin/login.pl'
    else:
        return 'https://ecf.%s.uscourts.gov/cgi-bin/login.pl' % court_id


def login(court_id, username, password):
    """Log into a PACER jurisdiction. Return cookies for the user."""
    s = requests.session()
    url = make_login_url(court_id)
    logger.info("Logging into: %s at %s" % (court_id, url))
    r = s.post(
        url,
        headers={'User-Agent': 'Juriscraper'},
        verify=False,
        timeout=60,
        files={
            'login': ('', username),
            'key': ('', password)
        },
    )
    if 'Invalid ID or password' in r.text:
        raise BadLoginException(r.text)

    # The cookie value is in the HTML. Extract it.
    m = re.search('PacerSession=(\w+);', r.text)
    if m is not None:
        return make_pacer_cookie_dict('PacerSession', m.group(1))
