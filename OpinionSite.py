from AbstractSite import AbstractSite
from juriscraper.lib.string_utils import clean_string, harmonize


class OpinionSite(AbstractSite):
    """Contains generic methods for scraping data. Should be extended by all
    scrapers.

    Should not contain lists that can't be sorted by the _date_sort function."""

    def __init__(self):
        super(OpinionSite, self).__init__()

        # Scraped metadata
        self.adversary_numbers = None
        self.case_dates = None
        self.case_names = None
        self.causes = None
        self.dispositions = None
        self.divisions = None
        self.docket_attachment_numbers = None
        self.docket_document_numbers = None
        self.docket_numbers = None
        self.download_urls = None
        self.judges = None
        self.lower_courts = None
        self.lower_court_judges = None
        self.lower_court_numbers = None
        self.nature_of_suit = None
        self.neutral_citations = None
        self.precedential_statuses = None
        self.summaries = None
        self.west_citations = None
        self.west_state_citations = None

    def parse(self):
        if self.status != 200:
            # Run the downloader if it hasn't been run already
            self.html = self._download()
        self.adversary_numbers = self._get_adversary_numbers()
        self.case_dates = self._get_case_dates()
        self.case_names = self._get_case_names()
        self.causes = self._get_causes()
        self.dispositions = self._get_dispositions()
        self.divisions = self._get_divisions()
        self.docket_attachment_numbers = self._get_docket_attachment_numbers()
        self.docket_document_numbers = self._get_docket_document_numbers()
        self.docket_numbers = self._get_docket_numbers()
        self.download_urls = self._get_download_urls()
        self.judges = self._get_judges()
        self.lower_courts = self._get_lower_courts()
        self.lower_court_judges = self._get_lower_court_judges()
        self.lower_court_numbers = self._get_lower_court_numbers()
        self.nature_of_suit = self._get_nature_of_suit()
        self.neutral_citations = self._get_neutral_citations()
        self.precedential_statuses = self._get_precedential_statuses()
        self.summaries = self._get_summaries()
        self.west_citations = self._get_west_citations()
        self.west_state_citations = self._get_west_state_citations()
        super(OpinionSite, self).parse()
        return self

    def _clean_attributes(self):
        """Iterate over attribute values and clean them"""
        for item in [self.adversary_numbers, self.causes, self.dispositions,
                     self.divisions, self.docket_attachment_numbers,
                     self.docket_document_numbers, self.docket_numbers,
                     self.judges, self.lower_courts, self.lower_court_judges,
                     self.lower_court_numbers, self.nature_of_suit,
                     self.neutral_citations, self.summaries,
                     self.west_citations, self.west_state_citations]:
            if item is not None:
                item[:] = [clean_string(sub_item) for sub_item in item]
        if self.case_names is not None:
            self.case_names = [harmonize(clean_string(case_name))
                               for case_name in self.case_names]

    def _check_sanity(self):
        """Calls super, passing the fields that need verifying
            """
        super(OpinionSite, self)._check_sanity(
            required_attributes=['case_dates', 'case_names',
                                 'precedential_statuses',
                                 'download_urls'],
            all_attributes=['adversary_numbers', 'case_dates', 'case_names', 'causes',
                            'dispositions', 'divisions', 'docket_attachment_numbers',
                            'docket_document_numbers', 'docket_numbers',
                            'download_urls', 'judges', 'lower_courts',
                            'lower_court_judges', 'nature_of_suit',
                            'lower_court_numbers', 'neutral_citations',
                            'precedential_statuses', 'summaries', 'west_citations',
                            'west_state_citations'],
        )

    def _date_sort(self):
        """ This function sorts the object by date. It's a good candidate for
        re-coding due to violating DRY and because it works by checking for
        lists, limiting the kinds of attributes we can add to the object.
        """
        # Note that case_dates must be first for sorting to work.
        attributes = [self.case_dates, self.adversary_numbers, self.case_names,
                      self.causes, self.dispositions, self.divisions,
                      self.docket_attachment_numbers,
                      self.docket_document_numbers, self.docket_numbers,
                      self.download_urls, self.judges, self.lower_courts,
                      self.lower_court_judges, self.lower_court_numbers,
                      self.nature_of_suit, self.neutral_citations,
                      self.precedential_statuses, self.summaries,
                      self.west_citations, self.west_state_citations]

        if len(self.case_names) > 0:
            obj_list_attrs = [item for item in attributes
                              if isinstance(item, list)]
            zipped = zip(*obj_list_attrs)
            zipped.sort(reverse=True)
            i = 0
            obj_list_attrs = zip(*zipped)
            for item in attributes:
                if isinstance(item, list):
                    item[:] = obj_list_attrs[i][:]
                    i += 1

    def _get_adversary_numbers(self):
        # Common in bankruptcy cases where there are adversary proceedings.
        return None

    def _get_download_urls(self):
        return None

    def _get_case_dates(self):
        return None

    def _get_case_names(self):
        return None

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
        return None

    def _get_summaries(self):
        return None

    def _get_west_citations(self):
        return None

    def _get_west_state_citations(self):
        return None
