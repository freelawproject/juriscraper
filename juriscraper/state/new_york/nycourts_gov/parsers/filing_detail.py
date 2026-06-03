"""Parser for the Court-PASS filing-detail page (``parse_filing_detail``)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from jkent.common.deferred_validation import DeferredValidation
from jkent.common.parser import JKentParser
from jkent.data_types import XPath

from juriscraper.state.new_york.nycourts_gov.models import (
    NYCourtPassDocket,
    NYCourtPassFile,
)

from ._common import _parse_date_mdy

if TYPE_CHECKING:
    from jkent.common.page_element import PageElement


class FilingDetailParser(JKentParser[NYCourtPassDocket]):
    """Parse the filing-detail span (``cphMain_lbDetails2``) and ``gvFiles``.

    The filing-detail page is reached via the hidden ``bttnDetails``
    postback from the docket-detail page. It carries the decision-side
    fields (decision date, opinion by, citation, issues) and the file
    list. Both ``parse_docket_filing_detail`` and
    ``parse_filing_detail_from_docket`` extract from the same span id;
    this parser is shared between them.
    """

    SPAN_ID = "cphMain_lbDetails2"

    def __call__(
        self, page: PageElement
    ) -> list[DeferredValidation[NYCourtPassDocket]]:
        span_xpath = f"//span[@id='{self.SPAN_ID}']"

        caption_parts = page.query_strings(
            XPath(
                f"{span_xpath}//div[contains(@class, 'case-caption')]//text()"
            ),
            "case caption text",
            min_count=0,
        )
        case_name = " ".join(t.strip() for t in caption_parts if t.strip())

        detail_map: dict[str, str] = {}
        dt_elements = page.query(
            XPath(f"{span_xpath}//dl[contains(@class, 'case-details')]/dt"),
            "case-details dt",
            min_count=0,
        )
        for dt in dt_elements:
            label = dt.text_content().strip().rstrip(":").strip()
            if not label:
                continue
            value_parts = dt.query_strings(
                XPath("./following-sibling::dd[1]//text()"),
                "case-details value",
                min_count=0,
            )
            value = " ".join(p.strip() for p in value_parts if p.strip())
            detail_map[label.casefold()] = value

        def _m(label: str) -> str | None:
            v = detail_map.get(label.casefold())
            return v or None

        argument_date_str = _m("Argument Date")
        decision_date_str = _m("Decision Date")
        opinion_by = _m("Opinion By")
        official_citation = _m("Official Citation")

        if argument_date_str and not re.match(
            r"\d{2}/\d{2}/\d{4}", argument_date_str
        ):
            argument_date_str = None
        if decision_date_str and not re.match(
            r"\d{2}/\d{2}/\d{4}", decision_date_str
        ):
            decision_date_str = None

        issues = self._extract_issue_strings(
            page, f"{span_xpath}//p[contains(@class, 'case-issues-category')]"
        )
        issue_details = self._extract_issue_strings(
            page, f"{span_xpath}//p[contains(@class, 'case-issues-text')]"
        )

        detail_texts = page.query_strings(
            XPath(f"{span_xpath}//text()"), "filing detail text", min_count=0
        )
        marker_text = " ".join(
            t.strip() for t in detail_texts if t.strip()
        ).lower()
        no_files_for_case = (
            "there are no files available for this case" in marker_text
        )
        files = self._parse_files(page)

        return [
            NYCourtPassDocket.raw(
                case_name=case_name,
                argument_date=_parse_date_mdy(argument_date_str),
                decision_date=_parse_date_mdy(decision_date_str),
                opinion_by=opinion_by,
                official_citation=official_citation,
                issues=issues,
                issue_details=issue_details,
                no_files_for_case=no_files_for_case,
                files=files,
            )
        ]

    @staticmethod
    def _extract_issue_strings(page: PageElement, xpath: str) -> list[str]:
        """One ``str`` per ``<p>`` matching ``xpath`` (joined text content).

        The unclosed ``<style pdffontname=...>`` markers that used to leak
        downstream markup into these ``<p>`` elements are stripped upstream
        (see ``repair_pdffont_leakage``), so the DOM here is clean.
        """
        elements = page.query(XPath(xpath), "issue p", min_count=0)
        return [text for el in elements if (text := el.text_content().strip())]

    @staticmethod
    def _parse_files(
        page: PageElement,
    ) -> list[DeferredValidation[NYCourtPassFile]]:
        """Walk ``gvFiles`` and build NYCourtPassFile rows.

        ``docket_number`` is not on the page; the step injects it
        after pulling raw_data from this parser.
        ``document_number`` is computed as ``total_files - row_index`` —
        bottom-up numbering, matching the downstream pipeline.
        """
        files_info: list[dict] = []
        file_rows = page.query(
            XPath("//table[contains(@id, 'gvFiles')]//tr[position()>1]"),
            "file rows",
            min_count=0,
        )
        for j, file_row in enumerate(file_rows):
            file_cells = file_row.query(XPath("td"), "file cells", min_count=0)
            if len(file_cells) < 2:
                continue
            file_name = file_cells[0].text_content().strip()
            buttons = file_row.query(
                XPath(".//input[@type='submit']"),
                "download button",
                min_count=0,
            )
            enabled_buttons = [
                b for b in buttons if not b.get_attribute("disabled")
            ]
            available = len(enabled_buttons) > 0
            files_info.append(
                {
                    "file_name": file_name,
                    "available": available,
                    "row_index": j,
                }
            )

        total_files = len(files_info)
        return [
            NYCourtPassFile.raw(
                file_name=f["file_name"],
                file_index=f["row_index"],
                document_number=total_files - i,
                available=f["available"],
            )
            for i, f in enumerate(files_info)
        ]
