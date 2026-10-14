from collections.abc import Iterator, Mapping, Sequence
from datetime import date, datetime
from operator import itemgetter

from dateutil import parser
from pydantic import TypeAdapter, ValidationError
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import BackscrapeItem, SiteOptions, logger
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import RawOpinion
from juriscraper.lib.utils import (
    clean_attribute,
    sanity_check_case_names,
    sanity_check_dates,
    sanity_check_opinion_types,
)
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

_cluster_adapter = TypeAdapter(RawOpinion)


class ClusterSite(OpinionSiteLinear[BackscrapeItem]):
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
        "child_court": "child_courts",
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

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[BackscrapeItem]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.all_attributes = self._all_attrs
        # doing this will help us re-use `AbstractSite.parse``
        self._all_attrs = []

        # if set,  allow clustering when dates are not exactly the same
        self.cluster_by_date_max_days = 0

    @override
    def __iter__(self) -> Iterator[RawOpinion]:
        yield from self.cases

    @override
    def __str__(self) -> str:
        return str(self.cases)

    @override
    def __getitem__(self, i: int) -> RawOpinion:
        return self.cases[i]

    @override
    def __len__(self) -> int:
        return len(self.cases)

    def normalize_attribute_name(self, name: str) -> str:
        """If short-hand attribute names were used, normalize them into full form
        supported by AbstractSite

        :param name: a possible attribute name
        :return: the normalized name
        :raises: ValueError if the input name has no normalized form
        """
        if name in self.all_attributes:
            return name

        if bool(self.short_to_full_attribute_name.get(name)):
            return self.short_to_full_attribute_name[name]

        raise ValueError(f"Invalid normalized name '{name}'")

    @override
    def _clean_attributes(self) -> None:
        """Perform name normalization and standard attribute cleaning.
        Handles nested opinions and replaces ``cases`` with normalized records.
        """
        clusters = []
        for case in self.cases:
            cleaned: dict[str, object] = {}
            # Build normalized nested records without mutating the source cases.
            pending: list[tuple[Mapping[str, object], dict[str, object]]] = [
                (case, cleaned)
            ]
            while bool(pending):
                record, destination = pending.pop()
                for key, value in record.items():
                    normalized_name = self.normalize_attribute_name(key)
                    if normalized_name == "sub_opinions":
                        if not isinstance(value, list):
                            raise TypeError(
                                "Sub-opinions must be a list of records."
                            )
                        opinions: list[dict[str, object]] = []
                        for opinion in value:
                            if not isinstance(opinion, Mapping):
                                raise TypeError(
                                    "A sub-opinion must be a mapping."
                                )
                            child: dict[str, object] = {}
                            opinions.append(child)
                            pending.append((opinion, child))
                        destination[normalized_name] = opinions
                    else:
                        destination[normalized_name] = clean_attribute(
                            normalized_name, value
                        )
            # Null defaulted fields are filled by _post_parse, like absent ones.
            for field in (
                "case_name_shorts",
                "date_filed_is_approximate",
                "blocked_statuses",
                "precedential_statuses",
            ):
                if cleaned.get(field) is None:
                    cleaned.pop(field, None)
            try:
                clusters.append(_cluster_adapter.validate_python(cleaned))
            except ValidationError as exc:
                raise InsanityException(
                    f"Invalid opinion cluster: {exc}"
                ) from exc
        self.cases = clusters

    @override
    def _date_sort(self) -> None:
        """Orders cases by values of _req_attributes, beggining with date and name"""

        keyed_cases: list[
            tuple[tuple[date | str | bool, ...], RawOpinion]
        ] = []
        for case in self.cases:
            values = []
            for attr in self._req_attrs:
                value = case.get(attr, "")
                if not isinstance(value, date | str | bool):
                    raise InsanityException(
                        f"Invalid value for {attr}: {value!r}"
                    )
                values.append(value)
            keyed_cases.append((tuple(values), case))

        keyed_cases.sort(key=itemgetter(0), reverse=True)
        self.cases[:] = [case for _, case in keyed_cases]

    @override
    def _post_parse(self) -> None:
        """Let's use this hook to add default values for required attributes"""
        for case in self.cases:
            if "case_names" not in case:
                raise InsanityException(
                    "An opinion cluster must have a case name."
                )
            if not bool(case.get("case_name_shorts")):
                case["case_name_shorts"] = self.cnt.make_case_name_short(
                    case["case_names"]
                )
            if not bool(case.get("date_filed_is_approximate")):
                case["date_filed_is_approximate"] = False
            if not bool(case.get("blocked_statuses")):
                case["blocked_statuses"] = False
            if not bool(case.get("precedential_statuses")):
                if bool(self.status):
                    case["precedential_statuses"] = self.status
                else:
                    raise InsanityException(
                        f"No value for `precedential_statuses` for case {case}"
                    )

    @override
    def _make_hash(self) -> None:
        """Populate the expected self.case_names list; just before calling the parent
        _make_hash
        """
        self.case_names = []
        for case in self.cases:
            if "case_names" not in case:
                raise InsanityException(
                    "An opinion cluster must have a case name."
                )
            self.case_names.append(case["case_names"])
        super()._make_hash()

    @override
    def _check_sanity(self) -> None:
        """Perform standard validity checks. Handles nested objects

        Checks that
        - results exist
        - each case dictionary has all of the required attributes
        - case names are valid
        - dates are valid
        """
        if not bool(self.cases):
            self.no_results_warning()
            return

        for case in self.cases:
            for field in self._req_attrs:
                if case.get(field) is None:
                    # should only apply to `download_urls` for nested sub opinions
                    # but let's write the general case
                    opinions = case.get("sub_opinions")
                    if bool(opinions) and all(
                        op.get(field) is not None for op in opinions
                    ):
                        continue
                    raise InsanityException(
                        f"Case {case} has no value for required '{field}'"
                    )

        case_names = []
        dates_and_names = []
        for i in self.cases:
            if "case_names" not in i or "case_dates" not in i:
                raise InsanityException(
                    "An opinion cluster must have a name and date."
                )
            case_names.append(i["case_names"])
            dates_and_names.append(
                (
                    i["case_dates"],
                    i.get("case_names"),
                    i.get("date_filed_is_approximate"),
                )
            )

        sanity_check_case_names(case_names)
        sanity_check_dates(dates_and_names, str(self.court_id))

        # Check opinion type rules for clusters with sub_opinions
        for case in self.cases:
            if bool(opinions := case.get("sub_opinions")):
                sanity_check_opinion_types(opinions)

        logger.info(
            f"{self.court_id}: Successfully found {len(self.cases)} items."
        )

    def validate_cluster_dates(
        self, datestring1: str | date | None, datestring2: str | date | None
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
        if datestring1 is None or datestring2 is None:
            return False
        if bool(self.cluster_by_date_max_days):
            dt1 = (
                parser.parse(datestring1).date()
                if isinstance(datestring1, str)
                else datestring1
            )
            dt2 = (
                parser.parse(datestring2).date()
                if isinstance(datestring2, str)
                else datestring2
            )
            if isinstance(dt1, datetime):
                dt1 = dt1.date()
            if isinstance(dt2, datetime):
                dt2 = dt2.date()
            return abs((dt1 - dt2).days) < self.cluster_by_date_max_days
        else:
            return datestring1 == datestring2

    def cluster_opinions(
        self, case_dict: RawOpinion, possible_clusters: Sequence[RawOpinion]
    ) -> RawOpinion | None:
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
        if not bool(possible_clusters):
            return None

        for candidate_cluster in possible_clusters:
            for field in ("name", "docket", "date"):
                if field not in case_dict or field not in candidate_cluster:
                    raise KeyError(field)
            # all of these should be the same for this to be considered a cluster
            if (
                case_dict.get("name") != candidate_cluster.get("name")
                or case_dict.get("docket") != candidate_cluster.get("docket")
                or not self.validate_cluster_dates(
                    case_dict.get("date"), candidate_cluster.get("date")
                )
            ):
                continue

            # if the sub_opinions list does not exist yet, build it from the
            # existing candidate_cluster
            sub_opinions = candidate_cluster.get("sub_opinions")
            if not bool(sub_opinions):
                sub_opinions = []
                candidate_cluster["sub_opinions"] = sub_opinions
                sources = (candidate_cluster, case_dict)
            else:
                sources = (case_dict,)

            # add the new opinion to the cluster
            for source in sources:
                opinion: RawOpinion = {}
                if "type" in source:
                    opinion["type"] = source.pop("type")
                if "url" in source:
                    opinion["url"] = source.pop("url")
                if "per_curiam" in source:
                    opinion["per_curiam"] = source.pop("per_curiam")
                if "author" in source:
                    opinion["author"] = source.pop("author")
                if "joined_by" in source:
                    opinion["joined_by"] = source.pop("joined_by")
                sub_opinions.append(opinion)

            return candidate_cluster

        return None
