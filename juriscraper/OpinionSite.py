from collections.abc import Awaitable, Sequence
from datetime import date

from juriscraper.AbstractSite import AbstractSite


class OpinionSite(AbstractSite):
    """Contains generic methods for scraping data. Should be extended by all
    scrapers.

    Should not contain lists that can't be sorted by the _date_sort function.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.expected_content_types = ["application/pdf"]

        # Order of attributes is important as it affects the order of parsing.
        # Some methods rely on others having already been run.
        self._opt_attrs = [
            "adversary_numbers",
            "causes",
            "dispositions",
            "divisions",
            "docket_attachment_numbers",
            "docket_document_numbers",
            "docket_numbers",
            "judges",
            "lower_courts",
            "lower_court_ids",
            "lower_court_judges",
            "lower_court_numbers",
            "nature_of_suit",
            "citations",
            "parallel_citations",
            "summaries",
            "case_name_shorts",
            "child_courts",
            "authors",
            "joined_by",
            "per_curiam",
            "types",
            "other_dates",
            "attorneys",
            "headnotes",
            "content",
        ]
        self._req_attrs = [
            "case_dates",
            "case_names",
            "download_urls",
            "precedential_statuses",
            "blocked_statuses",
            "date_filed_is_approximate",
        ]
        # For date sorting to work, case_dates must be first in _all_attrs.
        self._all_attrs = self._req_attrs + self._opt_attrs

        # Set all metadata to None
        for attr in self._all_attrs:
            self.__setattr__(attr, None)

    def _get_adversary_numbers(self) -> Sequence[str | None] | None:
        # Common in bankruptcy cases where there are adversary proceedings.
        return None

    def _get_download_urls(self) -> Sequence[str] | Awaitable[Sequence[str]]:
        raise NotImplementedError(
            "`_get_download_urls()` must be implemented."
        )

    def _get_case_dates(self) -> Sequence[date | str | None]:
        raise NotImplementedError("`_get_case_dates()` must be implemented.")

    def _get_case_names(self) -> Sequence[str]:
        raise NotImplementedError("`_get_case_names()` must be implemented.")

    def _get_causes(self) -> Sequence[str | None] | None:
        return None

    def _get_dispositions(self) -> Sequence[str | None] | None:
        return None

    def _get_divisions(self) -> Sequence[str | None] | None:
        return None

    def _get_docket_attachment_numbers(
        self,
    ) -> Sequence[int | str | None] | None:
        return None

    def _get_docket_document_numbers(
        self,
    ) -> Sequence[int | str | None] | None:
        return None

    def _get_docket_numbers(self) -> Sequence[str | None] | None:
        return None

    def _get_judges(self) -> Sequence[str | None] | None:
        return None

    def _get_nature_of_suit(self) -> Sequence[str | None] | None:
        return None

    def _get_citations(self) -> Sequence[str | None] | None:
        return None

    def _get_parallel_citations(self) -> Sequence[str | None] | None:
        return None

    def _get_lower_courts(self) -> Sequence[str | None] | None:
        return None

    def _get_lower_court_ids(self) -> Sequence[str | None] | None:
        return None

    def _get_lower_court_judges(self) -> Sequence[str | None] | None:
        return None

    def _get_lower_court_numbers(self) -> Sequence[str | None] | None:
        return None

    def _get_precedential_statuses(self) -> Sequence[str]:
        raise NotImplementedError(
            "`_get_precedential_statuses()` must be implemented."
        )

    def _get_summaries(self) -> Sequence[str | None] | None:
        return None

    def _get_child_courts(self) -> Sequence[str | None] | None:
        return None

    def _get_authors(self) -> Sequence[str | None] | None:
        return None

    def _get_types(self) -> Sequence[str | None] | None:
        return None

    def _get_joined_by(self) -> Sequence[str | None] | None:
        return None

    def _get_per_curiam(self) -> Sequence[bool | None] | None:
        return None

    def _get_other_dates(self) -> Sequence[str | None] | None:
        return None

    def _get_attorneys(self) -> Sequence[str | None] | None:
        return None

    def _get_headnotes(self) -> Sequence[str | None] | None:
        return None

    def _get_content(self) -> Sequence[str | bytes | None] | None:
        return None

    def extract_from_text(self, scraped_text: str) -> dict:
        """Pass scraped text into function and return data as a dictionary

        :param scraped_text: Text of scraped content
        :return: dictionary of information
        """
        return {}

    def _get_date_filed_is_approximate(self):
        return [False] * len(self.case_names)
