from collections.abc import Sequence
from datetime import date

from typing_extensions import Unpack

from juriscraper.AbstractSite import AbstractSite, BackscrapeItem, SiteOptions
from juriscraper.lib.string_utils import CaseNameTweaker


class OralArgumentSite(AbstractSite[BackscrapeItem]):
    """Contains generic methods for scraping data. Should be extended by all
    scrapers.

    Should not contain lists that can't be sorted by the _date_sort function.
    """

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[BackscrapeItem]],
    ) -> None:
        super().__init__(cnt, user_agent, **kwargs)

        self.expected_content_types = ["audio/mpeg"]

        self._opt_attrs = [
            "docket_numbers",
            "judges",
            "case_name_shorts",
            "attorneys",
        ]
        self._req_attrs = [
            "case_dates",
            "case_names",
            "download_urls",
            "blocked_statuses",
        ]
        # For date sorting to work, case_dates must be the first item in _all_attrs.
        self._all_attrs = self._req_attrs + self._opt_attrs

        # Set all metadata to None
        for attr in self._all_attrs:
            self.__setattr__(attr, None)

    def _get_download_urls(self) -> Sequence[str]:
        raise NotImplementedError(
            "`_get_download_urls()` must be implemented."
        )

    def _get_case_dates(self) -> Sequence[date | str | None]:
        raise NotImplementedError("`_get_case_dates()` must be implemented.")

    def _get_case_names(self) -> Sequence[str]:
        raise NotImplementedError("`_get_case_names()` must be implemented.")

    def _get_docket_numbers(self) -> Sequence[str | None] | None:
        return None

    def _get_judges(self) -> Sequence[str | None] | None:
        return None

    def _get_attorneys(self) -> Sequence[str | None] | None:
        return None
