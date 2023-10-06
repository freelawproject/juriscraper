from httpx import Cookies


def normalize_cookies(cookies):
    """Takes cookies from Selenium or from Python HTTPX and
    converts them to dict.

    This throws away information that Selenium otherwise has (like the host and
    such), but a dict is essentially all we need.
    """
    httpx_cookies = {}
    if isinstance(cookies, list):
        # Selenium cookies
        for cookie in cookies:
            httpx_cookies[cookie["name"]] = cookie["value"]
    elif isinstance(cookies, Cookies):
        # HTTPX cookies. Convert to dict.
        httpx_cookies = dict(cookies)

    return httpx_cookies
