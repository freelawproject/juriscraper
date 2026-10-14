from collections.abc import Awaitable, Sequence
from datetime import date

from typing_extensions import override

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OralArgumentSite import OralArgumentSite


class OralArgumentSiteLinear(OralArgumentSite):
    """This class can be used for any site that needs to be scraped linearly,
    instead of, for example, with separate html path parsing getters. Sometimes
    it is just easier and less repetitive to scrape a site this way, in which
    case you can simply extend this class and implement _process_html().
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cases = []
        self.status: str | None = None

    @override
    def _process_html(self) -> None | Awaitable[None]:
        raise Exception(
            "Must implement _process_html() on OralArgumentSiteLinear child"
        )

    @override
    def _get_case_names(self) -> Sequence[str]:
        return [case["name"] for case in self.cases]

    @override
    def _get_download_urls(self) -> Sequence[str]:
        return [case["url"] for case in self.cases]

    @override
    def _get_case_dates(self) -> Sequence[date | None]:
        return [convert_date_string(case["date"]) for case in self.cases]

    @override
    def _get_docket_numbers(self) -> Sequence[str | None]:
        return [case["docket"] for case in self.cases]

    # optional getters below

    def _get_optional_field_by_id(self, id):
        if self.cases and id in self.cases[0]:
            return [case[id] for case in self.cases]

    @override
    def _get_judges(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("judge")

    @override
    def _get_attorneys(self) -> Sequence[str | None] | None:
        return self._get_optional_field_by_id("attorney")
