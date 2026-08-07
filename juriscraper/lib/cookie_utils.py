from httpx import Cookies


def normalize_cookies(cookies):
    """Takes cookies from Selenium or from Python HTTPX and
    converts them to dict.

    This throws away information that Selenium otherwise has (like the host and
    such), but a dict is essentially all we need.
    """
    if isinstance(cookies, Cookies):
        # HTTPX cookies. Convert to dict.
        return dict(cookies)
    httpx_cookies = {}
    if isinstance(cookies, list):
        # Selenium cookies
        for cookie in cookies:
            httpx_cookies[cookie["name"]] = cookie["value"]

    return httpx_cookies
