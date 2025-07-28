from requests.cookies import RequestsCookieJar


def normalize_cookies(cookies):
    """Takes cookies from Selenium or from Python Requests and
    converts them to dict.

    This throws away information that Selenium otherwise has (like the host and
    such), but a dict is essentially all we need.
    """
    requests_cookies = {}
    if isinstance(cookies, list):
        # Selenium cookies
        for cookie in cookies:
            requests_cookies[cookie["name"]] = cookie["value"]
    elif isinstance(cookies, RequestsCookieJar):
        # Requests cookies. Convert to dict.
        requests_cookies = dict(cookies)

    return requests_cookies
