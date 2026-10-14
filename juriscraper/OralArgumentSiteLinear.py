from collections.abc import Awaitable, Mapping, Sequence
from datetime import date
from typing import Literal, overload

from typing_extensions import Unpack, override

from juriscraper.AbstractSite import BackscrapeItem, SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker, convert_date_string
from juriscraper.lib.type_utils import RawOralArgument
from juriscraper.OralArgumentSite import OralArgumentSite


class OralArgumentSiteLinear(OralArgumentSite[BackscrapeItem]):
    """This class can be used for any site that needs to be scraped linearly,
    instead of, for example, with separate html path parsing getters. Sometimes
    it is just easier and less repetitive to scrape a site this way, in which
    case you can simply extend this class and implement _process_html().
    """

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[BackscrapeItem]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)
        self.cases: list[RawOralArgument] = []
        self.status: str | None = None

    @override
    def _process_html(self) -> None | Awaitable[None]:
        raise Exception(
            "Must implement _process_html() on OralArgumentSiteLinear child"
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
    def _get_download_urls(self) -> Sequence[str]:
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
    def _get_docket_numbers(self) -> Sequence[str | None]:
        return [case.get("docket") for case in self.cases]

    # optional getters below

    @overload
    def _get_optional_field_by_id(
        self, id: Literal["judge", "attorney"]
    ) -> Sequence[str | None] | None: ...

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
    def _get_attorneys(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("attorney")
