from juriscraper.AbstractSite import AbstractSite


class OralArgumentSite(AbstractSite):
    """Contains generic methods for scraping data. Should be extended by all
    scrapers.

    Should not contain lists that can't be sorted by the _date_sort function.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._opt_attrs = [
            "docket_numbers",
            "judges",
            "case_name_shorts",
        ]
        self._req_attrs = [
            "case_dates",
            "case_names",
            "download_urls",
            "blocked_statuses",
        ]
        # For date sorting to work, case_dates must be the first item in _all_attrs.
        self._all_attrs = self._req_attrs + self._opt_attrs

        # Set all metadata to None
        for attr in self._all_attrs:
            self.__setattr__(attr, None)

    def _get_download_urls(self):
        raise NotImplementedError(
            "`_get_download_urls()` must be implemented."
        )

    def _get_case_dates(self):
        raise NotImplementedError("`_get_case_dates()` must be implemented.")

    def _get_case_names(self):
        raise NotImplementedError("`_get_case_names()` must be implemented.")

    def _get_docket_numbers(self):
        return None

    def _get_judges(self):
        return None
