from itertools import chain, islice, tee, izip


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
