from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class OpinionSiteLinear(OpinionSite):
    """This class can be used for any site that needs to be scraped linearly,
    instead of, for example, with separate html path parsing getters. Sometimes
    it is just easier and less repetitive to scrape a site this way, in which
    case you can simply extend this class and implement _process_html().
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []
        self.status = None

    def _process_html(self):
        raise Exception(
            "Must implement _process_html() on OpinionSiteLinear child"
        )

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _get_case_dates(self):
        return [convert_date_string(case["date"]) for case in self.cases]

    def _get_date_filed_is_approximate(self):
        return [
            case.get("date_filed_is_approximate", False) for case in self.cases
        ]

    def _get_precedential_statuses(self):
        # first try to use status values set in cases dictionary
        try:
            return [case["status"] for case in self.cases]
        except AttributeError:
            pass
        except KeyError:
            pass
        # we fall back on using singular status defined in init,
        # which is all you need to do if all cases on the page
        # have the same status
        if not self.status:
            raise Exception(
                "Must define self.status in __init__ on OpinionSiteLinear child"
            )
        return [self.status] * len(self.cases)

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]

    # optional getters below

    def _get_optional_field_by_id(self, id):
        if self.cases and id in self.cases[0]:
            return [case[id] for case in self.cases]

    def _get_judges(self):
        return self._get_optional_field_by_id("judge")

    def _get_citations(self):
        return self._get_optional_field_by_id("citation")

    def _get_parallel_citations(self):
        return self._get_optional_field_by_id("parallel_citation")

    def _get_summaries(self):
        return self._get_optional_field_by_id("summary")

    def _get_lower_courts(self):
        return self._get_optional_field_by_id("lower_court")
