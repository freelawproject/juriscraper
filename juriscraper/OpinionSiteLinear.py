# -*- coding: utf-8 -*-

from juriscraper.OpinionSite import OpinionSite


class OpinionSiteLinear(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(OpinionSiteLinear, self).__init__(*args, **kwargs)
        self.cases = []
        self.status = None

    def _process_html(self):
        raise Exception('Must implement _process_html() on OpinionSiteLinear child')

    def _get_case_names(self):
        return [case['name'] for case in self.cases]

    def _get_download_urls(self):
        return [case['url'] for case in self.cases]

    def _get_case_dates(self):
        return [case['date'] for case in self.cases]

    def _get_precedential_statuses(self):
        if not self.status:
            raise Exception("Must define self.status in __init__ on OpinionSiteLinear child")
        return [self.status] * len(self.cases)

    def _get_docket_numbers(self):
        return [case['docket'] for case in self.cases]

    # optional getters below

    # def _get_optional_field_by_id(self, id):
    #     if self.cases and id in self.cases[0]:
    #         return [case[id] for case in self.cases]

    # def _get_judges(self):
    #     return self._get_optional_field_by_id('judge')

    # def _get_neutral_citations(self):
    #     return self._get_optional_field_by_id('neutral_citation')

