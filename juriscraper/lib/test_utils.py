# -*- coding: utf-8 -*-
import os
import sys
import warnings

from requests.exceptions import ConnectionError
from requests.models import Request, Response

from .exceptions import SlownessException

WARN_SLOW_SRAPERS = "TRAVIS" in os.environ
warnings.simplefilter("always")


class SlownessWarning(UserWarning):
    pass


class CompareFileGeneratedWarning(UserWarning):
    pass


class TooSlowWarning(SlownessWarning):
    pass


class MockRequest(Request):
    def __init__(self, url=None):
        super(Request, self).__init__()
        self.url = url
        #: Resulting :class:`HTTPError` of request, if one occurred.
        self.error = None

        #: Encoding to decode with when accessing r.content.
        self.encoding = None

        #: The :class:`Request <Request>` that created the Response.
        self.request = self

    def get(self):
        r = Response()
        try:
            with open(self.url, mode="rb") as stream:
                r._content = stream.read()
                #: Integer Code of responded HTTP Status.
                r.status_code = 200
                if self.url.endswith("json"):
                    r.headers["content-type"] = "application/json"
        except IOError as e:
            r.status_code = 404
            raise ConnectionError(e)

        r._content_consumed = True

        #: Final URL location of Response.
        r.url = self.url

        # Return the response.
        return r


def warn_or_crash_slow_parser(duration, warn_duration=1, max_duration=15):
    msg = ""
    if duration > max_duration:
        if sys.gettrace() is None and not WARN_SLOW_SRAPERS:
            # Only do this if we're not debugging. Debuggers make things slower
            # and breakpoints make things stop.
            raise SlownessException(
                "This scraper took {duration}s to test, which is more than "
                "the allowed speed of {max_duration}s. Please speed it up for "
                "tests to pass.".format(
                    duration=duration, max_duration=max_duration
                )
            )
        elif WARN_SLOW_SRAPERS:
            msg = " - WARNING: SLOW SCRAPER"
            wmsg = "WARNING: VERY SLOW SCRAPER (potential Error)"
            warnings.warn(wmsg, TooSlowWarning)
    elif duration > warn_duration:
        msg = " - WARNING: SLOW SCRAPER"
        warnings.warn("WARNING: SLOW SCRAPER", SlownessWarning)
    else:
        msg = ""
    return msg


def warn_generated_compare_file(path_to_compare_file):
    warning = "WARNING: GENERATED COMPARE FILE: %s" % path_to_compare_file
    warnings.warn(warning, CompareFileGeneratedWarning)
