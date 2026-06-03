"""Parser for the Court-PASS docket-detail page (``parse_docket_detail``)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from jkent.common.deferred_validation import DeferredValidation
from jkent.common.parser import JKentParser
from jkent.data_types import XPath

from juriscraper.state.new_york.nycourts_gov.models import (
    NYCourtPassAttorney,
    NYCourtPassDocket,
    NYCourtPassDocketEntry,
)

from ._common import _parse_date_mdy

if TYPE_CHECKING:
    from jkent.common.page_element import PageElement


class DocketDetailParser(JKentParser[NYCourtPassDocket]):
    """Parse the docket-detail span (``cphMain_lbDetails``).

    The docket-detail page carries the case caption, argument date,
    FILINGS table (docket_entries), and ATTORNEY DETAILS table
    (attorneys). Used from ``parse_docket_detail`` (enumerate flow) and
    ``parse_docket_detail_for_entry`` (docket_by_number flow).
    """

    SPAN_XPATH = "//span[@id='cphMain_lbDetails']"

    def __call__(
        self, page: PageElement
    ) -> list[DeferredValidation[NYCourtPassDocket]]:
        case_details_dl = f"{self.SPAN_XPATH}//dl[@class='case-details']"

        docket_links = page.query_strings(
            XPath(
                f"{self.SPAN_XPATH}//button[contains(@onclick, 'CallDetails')]//text()"
            ),
            "docket number",
            min_count=0,
        )
        docket_number: str | None = None
        for link_text in docket_links:
            dn_match = re.search(r"[A-Z]+-\d{4}-\d{5}", link_text)
            if dn_match:
                docket_number = dn_match.group(0)
                break

        arg_date_texts = page.query_strings(
            XPath(
                f"{case_details_dl}"
                "/dt[contains(text(),'Argument Date')]/following-sibling::dd[1]//text()"
            ),
            "argument date",
            min_count=0,
        )
        argument_date_str: str | None = None
        for t in arg_date_texts:
            t = t.strip()
            if re.match(r"\d{2}/\d{2}/\d{4}", t):
                argument_date_str = t
                break

        title_texts = page.query_strings(
            XPath(
                f"{case_details_dl}"
                "/dt[contains(text(),'Title')]/following-sibling::dd[1]//text()"
            ),
            "case title",
            min_count=0,
        )
        case_name = " ".join(t.strip() for t in title_texts if t.strip())

        docket_entries = self._parse_filings(page)
        attorneys = self._parse_attorneys(page)

        return [
            NYCourtPassDocket.raw(
                docket_number=docket_number,
                case_name=case_name,
                argument_date=_parse_date_mdy(argument_date_str),
                docket_entries=docket_entries,
                attorneys=attorneys,
            )
        ]

    def _parse_filings(
        self, page: PageElement
    ) -> list[DeferredValidation[NYCourtPassDocketEntry]]:
        filings_tables = page.query(
            XPath(
                f"{self.SPAN_XPATH}//table[.//strong[contains(text(),'FILINGS')]]"
            ),
            "filings table",
            min_count=0,
        )
        if not filings_tables:
            return []
        filing_rows = filings_tables[0].query(
            XPath(".//tr[td[not(@colspan)]]"),
            "filing data rows",
            min_count=0,
        )
        entries: list[DeferredValidation[NYCourtPassDocketEntry]] = []
        for filing_row in filing_rows:
            cells = filing_row.query(XPath("td"), "filing cells", min_count=0)
            if len(cells) < 4:
                continue
            entries.append(
                NYCourtPassDocketEntry.raw(
                    filing_type=cells[0].text_content().strip(),
                    party=cells[1].text_content().strip() or None,
                    date_due=_parse_date_mdy(cells[2].text_content()),
                    date_received=_parse_date_mdy(cells[3].text_content()),
                )
            )
        return entries

    def _parse_attorneys(
        self, page: PageElement
    ) -> list[DeferredValidation[NYCourtPassAttorney]]:
        att_tables = page.query(
            XPath(
                f"{self.SPAN_XPATH}"
                "//table[.//strong[contains(text(),'ATTORNEY DETAILS')]]"
            ),
            "attorney table",
            min_count=0,
        )
        if not att_tables:
            return []
        all_rows = att_tables[0].query(
            XPath(".//tr"), "attorney rows", min_count=0
        )
        attorneys: list[DeferredValidation[NYCourtPassAttorney]] = []
        current: dict[str, str | None] = {}
        for row in all_rows:
            cells = row.query(XPath("td"), "cells", min_count=0)
            if not cells:
                continue

            first_text = cells[0].text_content().strip()
            if "ATTORNEY DETAILS" in first_text:
                continue

            colspan = cells[0].get_attribute("colspan")
            if colspan and int(colspan) >= 2:
                if current.get("party_name"):
                    attorneys.append(self._build_attorney(current))
                current = {}
                continue

            if len(cells) < 2:
                continue

            label = cells[0].text_content().strip().rstrip(":")
            value = cells[1].text_content().strip()

            if label == "Party Name":
                if current.get("party_name"):
                    attorneys.append(self._build_attorney(current))
                current = {
                    "party_name": value,
                    "party_role": "",
                    "firm": None,
                    "attorney_name": None,
                    "address": None,
                    "phone": None,
                }
            elif label == "Party Role":
                current["party_role"] = value
            elif label == "Firm":
                current["firm"] = value or None
            elif label == "Attorney":
                current["attorney_name"] = value or None
            elif label == "Address":
                current["address"] = value or None
            elif label == "Phone":
                current["phone"] = value.strip() or None
            elif not label and value and current.get("address"):
                current["address"] += "\n" + value

        if current.get("party_name"):
            attorneys.append(self._build_attorney(current))
        return attorneys

    @staticmethod
    def _build_attorney(
        raw: dict,
    ) -> DeferredValidation[NYCourtPassAttorney]:
        return NYCourtPassAttorney.raw(
            party_name=raw["party_name"],
            party_role=raw.get("party_role", ""),
            firm=raw.get("firm"),
            attorney_name=raw.get("attorney_name"),
            address=raw.get("address"),
            phone=raw.get("phone"),
        )
