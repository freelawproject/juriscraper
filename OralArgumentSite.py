from AbstractSite import AbstractSite
from juriscraper.lib.string_utils import clean_string, harmonize


class OralArgumentSite(AbstractSite):
    """Contains generic methods for scraping data. Should be extended by all
    scrapers.

    Should not contain lists that can't be sorted by the _date_sort function.
    """

    def __init__(self):
        super(OralArgumentSite, self).__init__()

        # Scraped metadata
        self.case_dates = None
        self.case_names = None
        self.docket_numbers = None
        self.download_urls = None

    def parse(self):
        if self.status != 200:
            # Run the downloader if it hasn't been run already
            self.html = self._download()
        self.case_dates = self._get_case_dates()
        self.case_names = self._get_case_names()
        self.docket_numbers = self._get_docket_numbers()
        self.download_urls = self._get_download_urls()

        super(OralArgumentSite, self).parse()
        return self

    def _clean_attributes(self):
        """Iterate over attribute values and clean them"""
        for item in [self.docket_numbers,]:
            if item is not None:
                item[:] = [clean_string(sub_item) for sub_item in item]
        if self.case_names is not None:
            self.case_names = [harmonize(clean_string(case_name))
                               for case_name in self.case_names]

    def _check_sanity(self):
        """Calls super, passing the fields that need verifying
        """
        super(OralArgumentSite, self)._check_sanity(
            required_attributes=['case_dates', 'case_names',
                                 'download_urls'],
            all_attributes=['case_dates', 'case_names', 'docket_numbers',
                            'download_urls'],
        )

    def _date_sort(self):
        """ This function sorts the object by date. It's a good candidate for
        re-coding due to violating DRY and because it works by checking for
        lists, limiting the kinds of attributes we can add to the object.
        """
        # Note that case_dates must be first for sorting to work.
        attributes = [self.case_dates, self.case_names,
                      self.docket_numbers, self.download_urls,]

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

    def _get_download_urls(self):
        return None

    def _get_case_dates(self):
        return None

    def _get_case_names(self):
        return None

    def _get_docket_numbers(self):
        return None
