from __future__ import annotations

from collections.abc import Awaitable, Mapping, Sequence
from datetime import date
from typing import Literal, overload

from typing_extensions import Unpack, override

from juriscraper.AbstractSite import BackscrapeItem, SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, convert_date_string
from juriscraper.lib.type_utils import RawOpinion
from juriscraper.OpinionSite import OpinionSite


class OpinionSiteLinear(OpinionSite[BackscrapeItem]):
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
        "lower_court_id",
        "lower_court_number",
        "lower_court_judge",
        "author",
        "per_curiam",
        "type",
        "joined_by",
        "other_date",
        "attorney",
        "headnote",
        # the downloaded content from download_url
        # cl_scrape_opinions is ready to consume this if present
        "content",
    }

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[BackscrapeItem]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.cases: list[RawOpinion] = []
        self.status: str | None = None

    @override
    def _process_html(self) -> None | Awaitable[None]:
        raise Exception(
            "Must implement _process_html() on OpinionSiteLinear child"
        )

    @override
    def _get_case_names(self) -> Sequence[str]:
        names = []
        for case in self.cases:
            if "name" not in case:
                raise KeyError("name")
            names.append(case["name"])
        return names

    @override
    def _get_download_urls(self) -> Sequence[str] | Awaitable[Sequence[str]]:
        urls = []
        for case in self.cases:
            if "url" not in case:
                raise KeyError("url")
            urls.append(case["url"])
        return urls

    @override
    def _get_case_dates(self) -> Sequence[date | None]:
        dates = []
        for case in self.cases:
            if "date" not in case:
                raise KeyError("date")
            value = case["date"]
            dates.append(
                convert_date_string(value) if isinstance(value, str) else value
            )
        return dates

    @override
    def _get_date_filed_is_approximate(self) -> Sequence[bool]:
        return [
            case.get("date_filed_is_approximate", False) for case in self.cases
        ]

    @override
    def _get_precedential_statuses(self) -> Sequence[str]:
        # first try to use status values set in cases dictionary
        statuses = [
            status
            for case in self.cases
            if (status := case.get("status")) is not None
        ]
        if len(statuses) == len(self.cases):
            return statuses
        # we fall back on using singular status defined in init,
        # which is all you need to do if all cases on the page
        # have the same status
        if not bool(self.status):
            raise Exception(
                "Must define self.status in __init__ on OpinionSiteLinear child"
            )
        return [self.status] * len(self.cases)

    @override
    def _get_docket_numbers(self) -> Sequence[str | None]:
        return [case.get("docket") for case in self.cases]

    # optional getters below

    @overload
    def _get_optional_field_by_id(
        self,
        id: Literal[
            "judge",
            "citation",
            "parallel_citation",
            "summary",
            "child_court",
            "lower_court",
            "lower_court_id",
            "lower_court_judge",
            "lower_court_number",
            "nature_of_suit",
            "cause",
            "disposition",
            "division",
            "adversary_number",
            "author",
            "joined_by",
            "type",
            "other_date",
            "attorney",
            "headnote",
        ],
    ) -> Sequence[str | None] | None: ...

    @overload
    def _get_optional_field_by_id(
        self, id: Literal["docket_document_number", "docket_attachment_number"]
    ) -> Sequence[int | str | None] | None: ...

    @overload
    def _get_optional_field_by_id(
        self, id: Literal["per_curiam"]
    ) -> Sequence[bool | None] | None: ...

    @overload
    def _get_optional_field_by_id(
        self, id: Literal["content"]
    ) -> Sequence[str | bytes | None] | None: ...

    @overload
    def _get_optional_field_by_id(
        self, id: str
    ) -> Sequence[object] | None: ...

    def _get_optional_field_by_id(self, id: str) -> Sequence[object] | None:
        cases: Sequence[Mapping[str, object]] = self.cases
        if bool(cases) and id in cases[0]:
            return [case[id] for case in cases]
        return None

    @override
    def _get_judges(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("judge")

    @override
    def _get_citations(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("citation")

    @override
    def _get_parallel_citations(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("parallel_citation")

    @override
    def _get_summaries(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("summary")

    @override
    def _get_child_courts(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("child_court")

    @override
    def _get_lower_courts(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("lower_court")

    @override
    def _get_lower_court_ids(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("lower_court_id")

    @override
    def _get_lower_court_judges(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("lower_court_judge")

    @override
    def _get_lower_court_numbers(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("lower_court_number")

    @override
    def _get_nature_of_suit(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("nature_of_suit")

    @override
    def _get_docket_document_numbers(
        self,
    ) -> Sequence[int | str | None] | None:
        return self._get_optional_field_by_id("docket_document_number")

    @override
    def _get_docket_attachment_numbers(
        self,
    ) -> Sequence[int | str | None] | None:
        return self._get_optional_field_by_id("docket_attachment_number")

    @override
    def _get_causes(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("cause")

    @override
    def _get_dispositions(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("disposition")

    @override
    def _get_divisions(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("division")

    @override
    def _get_adversary_numbers(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("adversary_number")

    @override
    def _get_authors(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("author")

    @override
    def _get_per_curiam(self) -> Sequence[bool | None] | None:
        return self._get_optional_field_by_id("per_curiam")

    @override
    def _get_joined_by(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("joined_by")

    @override
    def _get_types(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("type")

    @override
    def _get_other_dates(self) -> Sequence[str | None] | None:
        """Goes into OpinionCluster.other_dates, type: string"""
        return self._get_optional_field_by_id("other_date")

    @override
    def _get_attorneys(self) -> Sequence[str | None] | None:
        """Goes into OpinionCluster.attorneys, type: string"""
        return self._get_optional_field_by_id("attorney")

    @override
    def _get_headnotes(self) -> Sequence[str | None] | None:
        """Goes into OpinionCluster.headnotes, type: string"""
        return self._get_optional_field_by_id("headnote")

    @override
    def _get_content(self) -> Sequence[str | bytes | None] | None:
        """Goes into Opinion.html or Opinion.plain_text"""
        return self._get_optional_field_by_id("content")

    @override
    def _check_sanity(self) -> None:
        super()._check_sanity()
        # Check that all returned keys have the proper name to be used
        # in an Opinion / AbstractSite getter
        for case in self.cases:
            for key in case:
                if key not in self.valid_keys:
                    raise KeyError(
                        f"Invalid key '{key}' for case dictionary {self.__module__}"
                    )
