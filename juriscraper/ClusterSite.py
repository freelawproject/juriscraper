from typing import Optional

from dateutil import parser

from juriscraper.AbstractSite import logger
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.utils import (
    clean_attribute,
    sanity_check_case_names,
    sanity_check_dates,
    sanity_check_opinion_types,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class ClusterSite(OpinionSiteLinear):
    """
    Keeps an interface compatible with AbstractSite

    Main changes
    + uses a dict representation of a case; instead of the attribute list
        representation. We override
            __iter__
            __getitem__
            __len__
            important steps inside parse
                _clean_attributes
                _date_sort
                _check_sanity
                _get_case_name_shorts


    + each returned dict now represent a opinion cluster; no longer a plain opinion
        attribute
        Each opinion inside the cluster will have different values for
            - authors
            - joined by
            - types
            - download_urls

    For now, we keep the plural nomenclature 'authors', 'types', etc. This will
    make CL changes easier
    """

    short_to_full_attribute_name = {
        "name": "case_names",
        "date": "case_dates",
        "status": "precedential_statuses",
        "docket": "docket_numbers",
        "judge": "judges",
        "citation": "citations",
        "parallel_citation": "parallel_citations",
        "summary": "summaries",
        "child_courts": "child_courts",
        "disposition": "dispositions",
        "nature_of_suit": "nature_of_suit",
        "other_date": "other_dates",
        "attorney": "attorneys",
        "headnote": "headnotes",
        # lower court info
        "lower_court": "lower_courts",
        "lower_court_id": "lower_court_ids",
        "lower_court_judge": "lower_court_judges",
        "lower_court_number": "lower_court_numbers",
        "court_reporter": "court_reporter",
        # special field to hold the opinion list
        "sub_opinions": "sub_opinions",
        # opinion fields
        "author": "authors",
        "per_curiam": "per_curiam",
        "joined_by": "joined_by",
        "type": "types",
        "url": "download_urls",
        # present in OpinionSite but unused in regular case law flow
        "docket_document_number": "docket_document_numbers",
        "docket_attachment_number": "docket_attachment_numbers",
        "cause": "causes",
        "division": "divisions",
        "adversary_number": "adversary_numbers",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_attributes = self._all_attrs
        # doing this will help us re-use `AbstractSite.parse``
        self._all_attrs = []

        # if set,  allow clustering when dates are not exactly the same
        self.cluster_by_date_max_days = 0

    def __iter__(self):
        yield from self.cases

    def __str__(self):
        return self.cases

    def __getitem__(self, i):
        return self.cases[i]

    def __len__(self):
        return len(self.cases)

    def normalize_attribute_name(self, name: str) -> str:
        """If short-hand attribute names were used, normalize them into full form
        supported by AbstractSite

        :param name: an possible attribute name
        :return: the normalized name
        :raises: ValueError if the input name has no normalized form
        """
        if name in self.all_attributes:
            return name

        if self.short_to_full_attribute_name.get(name):
            return self.short_to_full_attribute_name[name]

        raise ValueError(f"Invalid normalized name '{name}'")

    def _clean_attributes(self):
        """Perform name normalization and standard attribute cleaning.
        Handles nested opinion objects
        """
        cases = []
        for case in self.cases:
            cleaned_case = {}
            for key, value in case.items():
                normalized_name = self.normalize_attribute_name(key)

                # handle sub opinion lists
                if isinstance(value, list):
                    sub_opinion_list = []
                    for sub_opinion in value:
                        sub_op = {}
                        for k, v in sub_opinion.items():
                            normalized_opinion_key = (
                                self.normalize_attribute_name(k)
                            )
                            sub_op[normalized_opinion_key] = clean_attribute(
                                normalized_opinion_key, v
                            )

                        sub_opinion_list.append(sub_op)
                    cleaned_case[normalized_name] = sub_opinion_list
                else:
                    cleaned_case[normalized_name] = clean_attribute(
                        normalized_name, value
                    )

            cases.append(cleaned_case)

        self.cases = cases

    def _date_sort(self):
        """Orders cases by values of _req_attributes, beggining with date and name"""
        self.cases.sort(
            key=lambda case: tuple(
                case.get(attr, "") for attr in self._req_attrs
            ),
            reverse=True,
        )

    def _post_parse(self):
        """Let's use this hook to add default values for required attributes"""
        for case in self.cases:
            if not case.get("case_name_short"):
                case["case_name_shorts"] = self.cnt.make_case_name_short(
                    case["case_names"]
                )
            if not case.get("date_filed_is_approximate"):
                case["date_filed_is_approximate"] = False
            if not case.get("blocked_statuses"):
                case["blocked_statuses"] = False
            if not case.get("precedential_statuses"):
                if self.status:
                    case["precedential_statuses"] = self.status
                else:
                    raise InsanityException(
                        f"No value for `precedential_statuses` for case {case}"
                    )

    def _make_hash(self):
        """Populate the expected self.cases list; just before calling the parent
        _make_hash
        """
        self.case_names = [i["case_names"] for i in self.cases]
        super()._make_hash()

    def _check_sanity(self):
        """Perform standard validity checks. Handles nested objects

        Checks that
        - results exist
        - each case dictionary has all of the required attributes
        - case names are valid
        - dates are valid
        """
        if len(self.cases) == 0:
            self.no_results_warning()
            return

        for case in self.cases:
            for field in self._req_attrs:
                if case.get(field) is None:
                    # should only apply to `download_urls` for nested sub opinions
                    # but let's write the general case
                    if case.get("sub_opinions") and all(
                        op.get(field) is not None
                        for op in case["sub_opinions"]
                    ):
                        continue
                    raise InsanityException(
                        f"Case {case} has no value for required '{field}'"
                    )

        case_names = []
        dates_and_names = []
        for i in self.cases:
            case_names.append(i["case_names"])
            dates_and_names.append(
                (
                    i["case_dates"],
                    i.get("date_filed_is_approximate"),
                    i.get("case_names"),
                )
            )

        sanity_check_case_names(case_names)
        sanity_check_dates(dates_and_names, self.court_id)

        # Check opinion type rules for clusters with sub_opinions
        for case in self.cases:
            if case.get("sub_opinions"):
                sanity_check_opinion_types(case["sub_opinions"])

        logger.info(
            f"{self.court_id}: Successfully found {len(self.cases)} items."
        )

    def validate_cluster_dates(
        self, datestring1: str, datestring2: str
    ) -> bool:
        """Check that 2 dates are close enough to cluster the opinions

        By default, it will check that the date strings are exactly the same

        If the instance attribute `cluster_by_date_max_days` is set to a value
        different from 0, it will try to parse the dates and check if the dates
        are close enough

        :param datestring1: a date string
        :param datestring2: another date strin
        :return: True if the datestrigs or their dates are close enough
        """
        if self.cluster_by_date_max_days:
            dt1 = parser.parse(datestring1)
            dt2 = parser.parse(datestring2)
            return abs((dt1 - dt2).days) < self.cluster_by_date_max_days
        else:
            return datestring1 == datestring2

    def cluster_opinions(
        self, case_dict: dict, possible_clusters: list[dict]
    ) -> Optional[dict]:
        """Try to cluster current opinion with previous opinions.
        To cluster, opinions should have the same
        - date
        - case name
        - docket number

        The caller should take care to propagate any metadata from the
        `case_dict` to the cluster proper

        :param case_dict: the case dict we will atempt to merge into any of the
            possible clusters
        :param possible_clusters: the existing clusters we will try to compare

        :return: None if we couldn't find a cluster
            the cluster dict if the current case dict was clustered
        """
        if not possible_clusters:
            return

        opinion_fields = ["type", "url", "per_curiam", "author", "joined_by"]

        for candidate_cluster in possible_clusters:
            # all of these should be the same for this to be considered a cluster
            if (
                case_dict["name"] != candidate_cluster["name"]
                or case_dict["docket"] != candidate_cluster["docket"]
                or not self.validate_cluster_dates(
                    case_dict["date"], candidate_cluster["date"]
                )
            ):
                continue

            # if the sub_opinions list does not exist yet, build it from the
            # existing candidate_cluster
            sub_opinions = candidate_cluster.get("sub_opinions")
            if not sub_opinions:
                candidate_cluster["sub_opinions"] = [
                    {
                        key: candidate_cluster.pop(key)
                        for key in opinion_fields
                        if key in candidate_cluster
                    }
                ]

            # add the new opinion to the cluster
            candidate_cluster["sub_opinions"].append(
                {
                    key: case_dict.pop(key)
                    for key in opinion_fields
                    if key in case_dict
                }
            )

            return candidate_cluster

        return
