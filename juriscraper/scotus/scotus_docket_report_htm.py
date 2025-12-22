import re
from collections import defaultdict
from typing import Any, Optional

from lxml import html
from lxml.html import HtmlElement

from juriscraper.lib.html_utils import strip_bad_html_tags_insecure
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.string_utils import clean_string, harmonize

from .scotus_docket_report_html import SCOTUSDocketReportHTML

logger = make_default_logger()


class SCOTUSDocketReportHTM(SCOTUSDocketReportHTML):
    """Parse SCOTUS docket HTM pages."""

    CONTACTS_TABLE_XPATH = (
        "//table[.//tr[td[1][contains(normalize-space(.), '~~Name')] "
        "and td[2][contains(normalize-space(.), '~~~~~~~Address')] "
        "and td[3][contains(normalize-space(.), '~~Phone')]]]"
    )
    HEADER_ROW_XPATH = (
        ".//tr[td[1][contains(normalize-space(.), '~~Name')] "
        "and td[2][contains(normalize-space(.), '~~~~~~~Address')] "
        "and td[3][contains(normalize-space(.), '~~Phone')]]"
    )

    def __init__(self, court_id: str = "scotus"):
        """Initialize the HTM report parser.

        :param court_id: The court ID.
        :return: None.
        """
        super().__init__(court_id=court_id)

    @property
    def metadata(self) -> dict[str, Any]:
        """Return normalized metadata extracted from the HTM docket.

        :return: A dict with the SCOTUS docket metadata.
        """
        if self.tree is None:
            return {}

        docket_number = None
        docket_title_text = self.tree.xpath(
            "(//table//tr/td[1][starts-with(normalize-space(.), 'No.')])[1]"
        )
        if docket_title_text:
            m = re.search(
                self.DOCKET_NUMBER_RE, docket_title_text[0].text_content()
            )
            docket_number = m.group(1).strip() if m else None

        # Case name
        title_tr = self._htm_row_for_label("Title:")
        title_td = (
            next(iter(title_tr.xpath("./td[2]")), None)
            if title_tr is not None
            else None
        )
        case_name = (
            harmonize(clean_string(self._join_nodes_content([title_td])))
            if title_td is not None
            else ""
        )

        # Dates and lower court info
        date_filed = self.normalize_date(self._htm_value_by_label("Docketed:"))
        lower_court = self._htm_value_by_label("Lower Ct:")

        # Lower court data
        lower_court_raw = self._htm_value_by_label(
            "Case Nos.:", allow_indent=True
        )
        lower_court_raw = (lower_court_raw or "").strip()
        lower_court_cleaned = None
        if lower_court_raw:
            lower_court_cleaned = self.clean_lower_court_cases(
                lower_court_raw.strip("()")
            )
        lower_court_decision_date = self.normalize_date(
            self._htm_value_by_label("Decision Date:", allow_indent=True)
        )
        lower_court_rehearing_denied_date = self.normalize_date(
            self._htm_value_by_label("Rehearing Denied:", allow_indent=True)
        )

        linked_with_label = "string(//tr[td[1][starts-with(normalize-space(.), 'Linked with')]])"
        linked_with_val = self.tree.xpath(linked_with_label).replace(
            "Linked with", ""
        )
        links = (linked_with_val or "").strip()
        return {
            "docket_number": docket_number,
            "capital_case": None,
            "date_filed": date_filed,
            "case_name": case_name or None,
            "links": links,
            "lower_court": lower_court or None,
            "lower_court_case_numbers_raw": lower_court_raw or None,
            "lower_court_case_numbers": lower_court_cleaned,
            "lower_court_decision_date": lower_court_decision_date,
            "lower_court_rehearing_denied_date": lower_court_rehearing_denied_date,
            "questions_presented": None,  # HTM version doesn’t have this link.
            "discretionary_court_decision": None,
        }

    def _build_docket_entry(
        self,
        date_str: str,
        description_td: Optional[HtmlElement],
        attachment_path: str,
        table_layout: bool = False,
    ) -> dict[str, Any]:
        """Build a normalized docket entry dict.

        :param date_str: Raw date string from the date cell.
        :param description_td: The <td> element containing the description.
        :param attachment_path: the path to select attachment anchors inside the
        description cell.
        :return: A dict containing the normalized docket entry.
        """

        description_html = ""
        if description_td is not None:
            # Select content up to first <br> and excluding .documentlinks;
            # fallback to whole cell.
            fragment = (
                self._parse_description_html(description_td).strip()
                or html.tostring(description_td, encoding="unicode").strip()
            )
            # Skip empty tds like <td ...></td>
            if not fragment or re.fullmatch(
                r"<td\b[^>]*>\s*</td>", fragment, flags=re.I
            ):
                description_html = ""
            else:
                description_html = fragment

            # If attachments with links are found in HTM dockets. Log an error
            # This is an opportunity to add support for it.
            if description_td is not None and description_td.xpath(
                attachment_path
            ):
                logger.error("SCOTUS HTM docket entry contains attachments.")

        description = ""
        raw = (description_html or "").strip()
        if raw:
            node = strip_bad_html_tags_insecure(raw)
            description = self._clean_whitespace(node.text_content())

        return {
            "date_filed": self.normalize_date(date_str),
            "document_number": None,
            "description": description,
            "description_html": description_html,
            "attachments": [],
        }

    @property
    def docket_entries(self) -> list[dict[str, Any]]:
        """Return docket entries from the HTM 'Proceedings and Orders' table.

        :return: List of dicts with date_filed, description, description_html, attachments.
        """
        if self.tree is None:
            return []

        tables = self.tree.xpath(
            "//table[.//tr[td[1][contains(normalize-space(.), '~~~Date~~~')] "
            "and td[2][contains(normalize-space(.), 'Proceedings')]]]"
        )
        if not tables:
            return []

        header_tr = next(
            iter(
                tables[0].xpath(
                    ".//tr[td[1][contains(normalize-space(.), '~~~Date~~~')] "
                    "and td[2][contains(normalize-space(.), 'Proceedings')]]"
                )
            ),
            None,
        )
        if header_tr is None:
            return []

        entries = []

        # Only iterate rows after the header within the same table
        for tr in header_tr.itersiblings(tag="tr"):
            tds = tr.xpath("./td")
            if not tds:
                continue
            date_str = self._clean_whitespace(tds[0].text_content())
            desc_td = tds[1]

            # Build the entry
            entries.append(
                self._build_docket_entry(
                    date_str=date_str,
                    description_td=desc_td,
                    attachment_path=".//a[@href]",
                )
            )

        return entries

    def _build_htm_attorney(
        self,
        current_attorney: Optional[dict[str, Any]],
    ) -> Optional[dict[str, Any]]:
        """Complete an attorney dict from the HTM Contacts table.

        :param current_attorney: The in-progress attorney dict with initial values.
        :return: The current_attorney dict.
        """
        if current_attorney is None:
            return None

        lines = current_attorney.pop("_raw_lines", [])
        email = current_attorney.pop("_email", None)

        # Filter lines: remove lines with IDs like "#1098260" and inline email if present.
        filtered_lines = []
        for ln in lines:
            if email is None:
                m = self.EMAIL_RE.search(ln)
                if m:
                    email = m.group(0)
                    continue
            if self.ID_RE.search(ln):
                continue
            if ln:
                filtered_lines.append(ln)

        title, start_add_idx = self._parse_address_title(filtered_lines)
        partial_address = self._parse_address_lines(
            filtered_lines, start_add_idx
        )

        addr_lines = partial_address.address_lines
        current_attorney.update(
            {
                "title": title,
                "address": ", ".join(addr_lines) if addr_lines else None,
                "city": partial_address.city,
                "state": partial_address.state,
                "zip": partial_address.zip_code,
                "email": email,
            }
        )
        return current_attorney

    @property
    def parties(self) -> list[dict[str, Any]]:
        """Return parties grouped by type for HTM pages.

        :return: List of dicts containing parties data.
        """
        if self.tree is None:
            return []

        # Locate the contacts table.
        contacts_tbl = next(
            iter(self.tree.xpath(self.CONTACTS_TABLE_XPATH)), None
        )
        if contacts_tbl is None:
            return []

        header_tr = next(iter(contacts_tbl.xpath(self.HEADER_ROW_XPATH)), None)
        if header_tr is None:
            return []

        parties_by_key = defaultdict(list)
        current_type = None
        current_attorney = None

        for tr in header_tr.itersiblings(tag="tr"):
            # Match table header e.g: "Attorneys for Petitioner:"
            header_text = self._clean_whitespace(
                "".join(tr.xpath("./td[1]//b/text()"))
            )
            if header_text:
                # Inside Petitioner, Respondent or Other parties.
                current_type = self._map_contacts_header_to_type(header_text)
                continue

            # Party name row. Finish previous attorney.
            party_name_re = r"^Party name:\s*"
            party_line = self._clean_whitespace(tr.text_content())
            if re.search(party_name_re, party_line, flags=re.I):
                current_party_name = re.sub(
                    party_name_re, "", party_line, flags=re.I
                ).strip()
                if current_attorney:
                    current_attorney = self._build_htm_attorney(
                        current_attorney
                    )
                    type_key = (current_type or "Other", current_party_name)
                    parties_by_key[type_key].append(current_attorney)
                continue

            tds = tr.xpath("./td")
            if not tds:
                continue

            # Extract normalized columns.
            name_col = (
                self._clean_whitespace(tds[0].text_content())
                if len(tds) >= 1
                else ""
            )
            address_col = (
                self._clean_whitespace(tds[1].text_content())
                if len(tds) >= 2
                else ""
            )
            phone_col = (
                self._clean_whitespace(tds[2].text_content())
                if len(tds) >= 3
                else None
            )

            # Email-only row appears in the address column.
            if (
                not name_col
                and address_col
                and self.EMAIL_RE.search(address_col)
            ):
                if current_attorney:
                    current_attorney["_email"] = self.EMAIL_RE.search(
                        address_col
                    ).group(0)
                continue

            # "Counsel of Record" marker row.
            if re.search(r"\bcounsel\s+of\s+record\b", name_col, re.I):
                if current_attorney:
                    current_attorney["is_counsel_of_record"] = True
                    if address_col:
                        current_attorney.setdefault("_raw_lines", []).append(
                            address_col
                        )
                continue

            # Beginning of a new attorney row.
            if name_col:
                current_attorney = {
                    "name": name_col or None,
                    "is_counsel_of_record": False,
                    "phone": phone_col or None,
                    "_raw_lines": [],
                    "_email": None,
                }
                if address_col:
                    current_attorney["_raw_lines"].append(address_col)
                continue

            # Address parsing continuation for the current attorney.
            if not name_col and address_col and current_attorney:
                current_attorney["_raw_lines"].append(address_col)
                continue

        return [
            {"type": party_type, "name": name, "attorneys": attorneys}
            for (party_type, name), attorneys in parties_by_key.items()
        ]

    def _htm_row_for_label(
        self, label: str, allow_indent: bool = False
    ) -> Optional[HtmlElement]:
        """Return the <tr> whose first <td> equals the given label.

        :param label: The exact label text, e.g. "Docketed:" or "Case Nos.:".
        :param allow_indent: If True, normalize non-breaking spaces before matching.
        :return: The <tr> element or None.
        """
        if self.tree is None:
            return None

        if allow_indent:
            # Allow \u00a0 for the first td cell text
            target_label = f"//tr[td][normalize-space(translate(string(td[1]), '\u00a0',' '))='{label}']"
        else:
            target_label = (
                f"//tr[td][normalize-space(string(td[1]))='{label}']"
            )

        return next(iter(self.tree.xpath(target_label)), None)

    def _htm_value_by_label(
        self, label: str, allow_indent: bool = False
    ) -> Optional[str]:
        """Get the value text in td[2] for a labeled row.

        :param label: The label text in td[1].
        :param allow_indent: True to allow labels with leading &nbsp;.
        :return: Cleaned value string or None.
        """
        tr = self._htm_row_for_label(label, allow_indent=allow_indent)
        if tr is None:
            return None
        val_td = next(iter(tr.xpath("./td[2]")), None)
        return (
            self._clean_whitespace(val_td.text_content())
            if val_td is not None
            else None
        )


def _main():
    """Parse a local HTML file and pretty-print normalized data.

    :return: None
    """
    import pprint
    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python -m juriscraper.scotus_docket_report_htm <filepath>"
        )
        sys.exit(1)

    parser = SCOTUSDocketReportHTM()
    with open(sys.argv[1], encoding="utf-8") as f:
        parser._parse_text(f.read())
    pprint.pprint(parser.data, indent=2)


if __name__ == "__main__":
    _main()
