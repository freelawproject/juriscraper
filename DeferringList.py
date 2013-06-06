class DeferringList(object):
    """This object can be used to do deferred loading of meta data in the case that a piece of meta data requires
    some special work to obtain.

    For an example of how this can be used, see juriscraper.opinions.united_states.state.tex
    """
    def __init__(self, *args, **kwargs):
        self._data = kwargs['seed']
        self._fetched_items = [False] * len(kwargs['seed'])
        self._fetching_function = kwargs['fetcher']

    def __iter__(self):
        for item in range(0, len(self._data)):
            if self._fetched_items[item]:
                yield self._data[item]
            else:
                # Go get the item using the fetching function
                new_val = self._fetching_function(self._data[item])
                self._data[item] = new_val
                self._fetched_items[item] = True
                yield new_val

    def __getitem__(self, item):
        if self._fetched_items[item]:
            return self._data[item]
        else:
            # Go get the item using the fetching function
            new_val = self._fetching_function(self._data[item])
            self._data[item] = new_val
            self._fetched_items[item] = True
            return new_val

    def __len__(self):
        return len(self._data)




