from juriscraper.AbstractSite import AbstractSite


class OpinionSite(AbstractSite):
    """Contains generic methods for scraping data. Should be extended by all
    scrapers.

    Should not contain lists that can't be sorted by the _date_sort function.
    """

    def __init__(self, *args, **kwargs):
        super(OpinionSite, self).__init__(*args, **kwargs)

        # Order of attributes is important as it affects the order of parsing.
        # Some methods rely on others having already been run.
        self._opt_attrs = [
            'adversary_numbers', 'causes', 'dispositions', 'divisions',
            'docket_attachment_numbers', 'docket_document_numbers',
            'docket_numbers', 'judges', 'lower_courts', 'lower_court_judges',
            'lower_court_numbers', 'nature_of_suit', 'neutral_citations',
            'summaries', 'west_citations', 'west_state_citations',
            'case_name_shorts',
        ]
        self._req_attrs = ['case_dates', 'case_names', 'download_urls',
                           'precedential_statuses', 'blocked_statuses',
                           'date_filed_is_approximate',]
        # For date sorting to work, case_dates must be first in _all_attrs.
        self._all_attrs = self._req_attrs + self._opt_attrs

        # Set all metadata to None
        for attr in self._all_attrs:
            self.__setattr__(attr, None)

    def _get_adversary_numbers(self):
        # Common in bankruptcy cases where there are adversary proceedings.
        return None

    def _get_download_urls(self):
        raise NotImplementedError('`_get_download_urls()` must be implemented.')

    def _get_case_dates(self):
        raise NotImplementedError('`_get_case_dates()` must be implemented.')

    def _get_case_names(self):
        raise NotImplementedError('`_get_case_names()` must be implemented.')

    def _get_causes(self):
        return None

    def _get_dispositions(self):
        return None

    def _get_divisions(self):
        return None

    def _get_docket_attachment_numbers(self):
        return None

    def _get_docket_document_numbers(self):
        return None

    def _get_docket_numbers(self):
        return None

    def _get_judges(self):
        return None

    def _get_nature_of_suit(self):
        return None

    def _get_neutral_citations(self):
        return None

    def _get_lower_courts(self):
        return None

    def _get_lower_court_judges(self):
        return None

    def _get_lower_court_numbers(self):
        return None

    def _get_precedential_statuses(self):
        raise NotImplementedError('`_get_precedential_statuses()` must be implemented.')

    def _get_summaries(self):
        return None

    def _get_west_citations(self):
        return None

    def _get_west_state_citations(self):
        return None

    def _get_date_filed_is_approximate(self):
        return [False] * len(self.case_names)
