import re
from itertools import chain, islice, tee

from six import string_types

from .string_utils import force_unicode

try:
    from itertools import izip
except ImportError:
    izip = zip


def previous_and_next(some_iterable):
    """Provide previous and next values while iterating a list.

    This is from: http://stackoverflow.com/a/1012089/64911

    This will allow you to lazily iterate a list such that as you iterate, you
    get a tuple containing the previous, current, and next value.
    """
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return izip(prevs, items, nexts)


def clean_court_object(obj):
    """Clean a list or dict that is part of a scraping response.

    Court data is notoriously horrible, so this function attempts to clean up
    common problems that it may have. You can pass in either a dict or a list,
    and it will be cleaned recursively.

    Supported cleanup includes:

    1. Removing spaces before commas.
    1. Stripping whitespace from the ends.
    1. Normalizing white space.
    1. Forcing unicode.

    :param obj: A dict or list containing string objects.
    :return: A dict or list with the string values cleaned.
    """
    if isinstance(obj, list):
        l = []
        for i in obj:
            l.append(clean_court_object(i))
        return l
    elif isinstance(obj, dict):
        d = {}
        for k, v in obj.items():
            d[k] = clean_court_object(v)
        return d
    elif isinstance(obj, string_types):
        s = " ".join(obj.strip().split())
        s = force_unicode(s)
        return re.sub("\s+,", ",", s)
    else:
        return obj
