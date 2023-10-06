import os
import sys
import warnings

from httpx import Response

from .exceptions import SlownessException

WARN_SLOW_SCRAPERS = "CI" in os.environ


class SlownessWarning(UserWarning):
    pass


class CompareFileGeneratedWarning(UserWarning):
    pass


class TooSlowWarning(SlownessWarning):
    pass


def warn_or_crash_slow_parser(duration, warn_duration=1, max_duration=15):
    msg = ""
    if duration > max_duration:
        if sys.gettrace() is None and not WARN_SLOW_SCRAPERS:
            # Only do this if we're not debugging. Debuggers make things slower
            # and breakpoints make things stop.
            raise SlownessException(
                "This scraper took {duration:.3f}s to test, which is more than "
                "the allowed speed of {max_duration}s. Please speed it up for "
                "tests to pass.".format(
                    duration=duration, max_duration=max_duration
                )
            )
        elif WARN_SLOW_SCRAPERS:
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
    warning = f"WARNING: GENERATED COMPARE FILE: {path_to_compare_file}"
    warnings.warn(warning, CompareFileGeneratedWarning)


class MockResponse(Response):
    """Mock a Request Response"""

    def __init__(self, status_code, content=None, headers=None, request=None):
        self.status_code = status_code
        self._content = content
        self.headers = headers
        self.request = request
