from AbstractSite import AbstractSite


class OralArgumentSite(AbstractSite):
    """Contains generic methods for scraping data. Should be extended by all
    scrapers.

    Should not contain lists that can't be sorted by the _date_sort function.
    """

    def __init__(self):
        super(OralArgumentSite, self).__init__()

        self._opt_attrs = ['docket_numbers']
        self._req_attrs = ['case_dates', 'case_names', 'download_urls']
        # For date sorting to work, case_dates must be the first item in _all_attrs.
        self._all_attrs = self._req_attrs + self._opt_attrs

        # Set all metadata to None
        for attr in self._all_attrs:
            self.__setattr__(attr, None)

    def _get_download_urls(self):
        return None

    def _get_case_dates(self):
        return None

    def _get_case_names(self):
        return None

    def _get_docket_numbers(self):
        return None
