from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class OpinionSiteLinear(OpinionSite):
    """This class can be used for any site that needs to be scraped linearly,
    instead of, for example, with separate html path parsing getters. Sometimes
    it is just easier and less repetitive to scrape a site this way, in which
    case you can simply extend this class and implement _process_html().
    """

    # This class tries to simplify OpinionSiteLinear. Instead of using full
    # attribute names, we use shorthands. The keys must be properly named
    # for the getters to work, so this `valid_keys` will be used in an
    # extended check_sanity method
    valid_keys = {
        "name",
        "url",
        "date",
        "date_filed_is_approximate",
        "status",
        "docket",
        "judge",
        "citation",
        "parallel_citation",
        "summary",
        "lower_court",
        "child_court",
        "adversary_number",
        "division",
        "disposition",
        "cause",
        "docket_attachment_number",
        "docket_document_number",
        "nature_of_suit",
        "lower_court_number",
        "lower_court_judge",
        "author",
        "per_curiam",
        "type",
        "joined_by",
        "other_date",
        "attorney",
    }

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

    def _get_child_courts(self):
        return self._get_optional_field_by_id("child_court")

    def _get_lower_courts(self):
        return self._get_optional_field_by_id("lower_court")

    def _get_lower_court_judges(self):
        return self._get_optional_field_by_id("lower_court_judge")

    def _get_lower_court_numbers(self):
        return self._get_optional_field_by_id("lower_court_number")

    def _get_nature_of_suit(self):
        return self._get_optional_field_by_id("nature_of_suit")

    def _get_docket_document_numbers(self):
        return self._get_optional_field_by_id("docket_document_number")

    def _get_docket_attachment_numbers(self):
        return self._get_optional_field_by_id("docket_attachment_number")

    def _get_causes(self):
        return self._get_optional_field_by_id("cause")

    def _get_dispositions(self):
        return self._get_optional_field_by_id("disposition")

    def _get_divisions(self):
        return self._get_optional_field_by_id("division")

    def _get_adversary_numbers(self):
        return self._get_optional_field_by_id("adversary_number")

    def _get_authors(self):
        return self._get_optional_field_by_id("author")

    def _get_per_curiam(self):
        return self._get_optional_field_by_id("per_curiam")

    def _get_joined_by(self):
        return self._get_optional_field_by_id("joined_by")

    def _get_types(self):
        return self._get_optional_field_by_id("type")

    def _get_other_dates(self):
        """Goes into OpinionCluster.other_dates, type: string"""
        return self._get_optional_field_by_id("other_date")

    def _get_attorneys(self):
        """Goes into OpinionCluster.attorneys, type: string"""
        return self._get_optional_field_by_id("attorney")

    def _check_sanity(self):
        super()._check_sanity()
        # Check that all returned keys have the proper name to be used
        # in an Opinion / AbstractSite getter
        for case in self.cases:
            if isinstance(case, str):
                # happens with mich example files
                continue

            for key in case.keys():
                if key not in self.valid_keys:
                    raise KeyError(
                        f"Invalid key '{key}' for case dictionary {self.__module__}"
                    )
