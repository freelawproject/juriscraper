from juriscraper.AbstractSite import logger


class DeferringList(object):
    """This object can be used to do deferred loading of meta data in the case
    that a piece of meta data requires some special work to obtain.

    Note that since this inherits from object (rather than list), it won't be
    sorted by the _date_sort function. As a result, it's vital that the code
    using this object provide the seed data in sorted order. Failure to do so
    will result in mixed up data being sent to the caller -- a bad fate.

    For an example of how this can be used, see
    juriscraper.opinions.united_states.state.tex
    """

    def __init__(self, *args, **kwargs):
        logger.warn(
            "Using DeferringList object which cannot be sorted until "
            "fetched. Note that in usual processing, the fetching "
            "happens before the sorting, so this is OK."
        )
        logger.info(
            "DeferringList has %s entries to fetch." % len(kwargs["seed"])
        )
        self._data = kwargs["seed"]
        self._fetched_items = [False] * len(kwargs["seed"])
        self._fetching_function = kwargs["fetcher"]

    def __iter__(self):
        for item in range(0, len(self._data)):
            if self._fetched_items[item]:
                yield self._data[item]
            else:
                yield self.__getitem__(item)

    def __getitem__(self, item):
        if self._fetched_items[item]:
            return self._data[item]
        else:
            # Go get the item using the fetching function
            logger.info(
                "Getting deferred value from seed: %s" % self._data[item]
            )
            new_val = self._fetching_function(self._data[item])
            self._data[item] = new_val
            self._fetched_items[item] = True
            return new_val

    def __setitem__(self, key, value):
        if self._fetched_items[key]:
            self._data[key] = value
        else:
            raise AttributeError(
                "Cannot set item that has not yet been fetched."
            )

    def __delitem__(self, item):
        del self._data[item]
        del self._fetched_items[item]

    def __len__(self):
        return len(self._data)

    def __str__(self):
        return "<DeferringList %s>" % self.__dict__
