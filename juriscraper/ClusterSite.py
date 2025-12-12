from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class ClusterSite(OpinionSiteLinear):
    """ """

    def _get_authors(self):
        return self._get_optional_field_by_id("author")

    def _get_joined_by(self):
        return self._get_optional_field_by_id("joined_by")

    def _get_types(self):
        return self._get_optional_field_by_id("type")

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _check_sanity(self):
        self.no_results_warning()

        pass

    def _date_sort(self):
        pass

    def _clean_attributes(self):
        pass

    # def parse(self):
    #     if not self.downloader_executed:
    #         # Run the downloader if it hasn't been run already
    #         self.html = self._download()

    #         # Process the available html (optional)
    #         self._process_html()

    #     # Set the attribute to the return value from _get_foo()
    #     # e.g., this does self.case_names = _get_case_names()
    #     for attr in self._all_attrs:
    #         self.__setattr__(attr, getattr(self, f"_get_{attr}")())

    #     self._clean_attributes()
    #     if "case_name_shorts" in self._all_attrs:
    #         # This needs to be done *after* _clean_attributes() has been run.
    #         # The current architecture means this gets run twice. Once when we
    #         # iterate over _all_attrs, and again here. It's pretty cheap though.
    #         self.case_name_shorts = self._get_case_name_shorts()
    #     self._post_parse()
    #     self._check_sanity()
    #     self._date_sort()
    #     self._make_hash()
    #     return self
