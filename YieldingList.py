class YieldingList(list):
    def __init__(self, *args, **kwargs):
        self._data = kwargs['seed']
        self._fetched_items = [False] * len(kwargs['seed'])
        self._fetching_function = kwargs['fetcher']

    def __iter__(self):
        for i in range(0, len(self._data)):
            if self._fetched_items[i]:
                yield self._data[i]
            else:
                self._fetching_function(i)

    def __getitem__(self, item):
        if self._fetched_items[item]:
            yield self._data[i]
        else:
            # Go get the item using the fetching function
            self._fetching_function(i)

    def __len__(self):
        return len(self._data)




