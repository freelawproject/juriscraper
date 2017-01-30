"""
Helper functions for interacting with PACER via the Requests library
"""
from requests import Request


def post_to_pacer(session, url, data, verify=False, timeout=300):
    """
    Do a POST to PACER in a way that won't make them cry.
    :param session: preconfigured Requests session, already auth'd to PACER
    :param url: url to POST to
    :param data: dict of the data to POST
    :param verify:
    :param timeout:
    :return: Requests Response object
    """
    req = Request('POST', url, files=data)
    prepped = session.prepare_request(req)
    prepped.body = prepped.body.decode('ascii').replace('; filename=""', '')
    prepped.headers['Content-Length'] = len(prepped.body)

    return session.send(prepped, verify=verify, timeout=timeout)
