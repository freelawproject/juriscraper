"""Parser for the Court-PASS docket-results grid (``parse_docket_results``)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from kent.common.deferred_validation import DeferredValidation
from kent.common.parser import KentParser

from juriscraper.state.new_york.nycourts_gov.models import NYCourtPassDocket

from ._common import _parse_date_mdy

if TYPE_CHECKING:
    from kent.common.page_element import PageElement


class DocketResultsParser(KentParser[NYCourtPassDocket]):
    """Parse each row of the ``gvResults`` docket search grid.

    Returns one ``DeferredValidation[NYCourtPassDocket]`` per data row,
    carrying the fields that survive into NYCourtPassDocket:
    ``case_short_name``, ``argument_date``, ``aria_case_info``, plus
    ``search_row`` (the 0-based row index within this page of search results).
    """

    def __call__(
        self, page: PageElement
    ) -> list[DeferredValidation[NYCourtPassDocket]]:
        data_rows = page.query_xpath(
            "//table[contains(@id, 'gvResults')]"
            "//tr[.//input[contains(@id, 'btnSelect')]]",
            "docket data rows",
            min_count=0,
        )
        results: list[DeferredValidation[NYCourtPassDocket]] = []
        for i, row in enumerate(data_rows):
            cells = row.query_xpath("td", "row cells", min_count=0)
            if len(cells) < 3:
                continue
            case_title = " ".join(cells[1].text_content().split())
            argument_date_str = cells[2].text_content().strip()
            select_buttons = row.query_xpath(
                ".//input[contains(@id, 'btnSelect')]",
                "select button",
                min_count=0,
            )
            aria_case_info = (
                select_buttons[0].get_attribute("aria-label")
                if select_buttons
                else None
            )
            results.append(
                NYCourtPassDocket.raw(
                    case_short_name=case_title or None,
                    argument_date=_parse_date_mdy(argument_date_str),
                    aria_case_info=aria_case_info,
                    search_row=i,
                )
            )
        return results
