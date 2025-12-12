import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Optional

from lxml import html
from lxml.html import HtmlElement

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import clean_html, strip_bad_html_tags_insecure
from juriscraper.lib.string_utils import clean_string, harmonize
from juriscraper.scotus import SCOTUSDocketReport


@dataclass
class ContactAddress:
    title: Optional[str]
    address_lines: list[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    email: Optional[str]


class SCOTUSDocketReportHTML(SCOTUSDocketReport):
    """Parse SCOTUS docket HTML."""

    EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
    ID_RE = re.compile(r"#\s*[A-Za-z0-9-]+\b")
    ADDRESS_NUMBER = re.compile(
        r"\b(\d{1,6}(?:-\d{1,6})?(?:\s+\d+\/\d+)?[A-Za-z]?)\b"
    )
    ADDRESS_RE = r"([^,]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$"
    DOCKET_NUMBER_RE = r"No\.\s*([^\s<]+)"

    def __init__(self, court_id: str = "scotus"):
        """Initialize the HTML report parser."""
        super().__init__(court_id=court_id)
        self.tree = None

    def _parse_text(self, text: str) -> None:
        """Parse raw HTML and store a lxml tree.

        :param text: The raw HTML unicode object.
        :return: None
        """
        text = clean_html(text)
        self.tree = html.fromstring(text or "")

    @property
    def metadata(self) -> dict[str, Any]:
        """Return normalized docket metadata extracted from HTML.

        :return: A dict with the SCOTUS docket metadata.
        """

        if self.tree is None:
            return {}

        docket_title_text = self._join_nodes_content(
            self.tree.xpath(
                "//table[@id='docketinfo']//span[contains(@class,'DocketInfoTitle')]"
            )
        )
        docket_number = None
        if docket_title_text:
            m = re.search(self.DOCKET_NUMBER_RE, docket_title_text)
            docket_number = m.group(1).strip() if m else None

        case_name = clean_string(
            harmonize(
                self._clean_whitespace(
                    self._join_nodes_content(
                        self.tree.xpath(
                            "//table[@id='docketinfo']//span[@class='title']"
                        )
                    )
                )
            )
        )

        docketed_str = self._td_value_by_label("Docketed:")
        date_filed = self.normalize_date(docketed_str)

        linked_with_val = self._td_value_by_label("Linked with:")
        if not linked_with_val:
            # Sometimes the value is in the same cell: Linked with 16A827
            target_label = "string(//table[@id='docketinfo']//tr[td[1]/span[starts-with(normalize-space(.), 'Linked with')]])"
            linked_with_val = self.tree.xpath(target_label).replace(
                "Linked with", ""
            )
        links = (linked_with_val or "").strip()

        lower_court = self._td_value_by_label("Lower Ct:")
        # Lower court case numbers
        lower_court_raw = self._td_value_by_label(
            "Case Numbers:", allow_indent=True
        )
        lower_court_raw = (lower_court_raw or "").strip()
        lower_court_cleaned = None
        if lower_court_raw:
            lower_court_text = lower_court_raw.strip("()")
            lower_court_cleaned = self.clean_lower_court_cases(
                lower_court_text
            )

        # Decision dates
        lower_court_decision_date = self.normalize_date(
            self._td_value_by_label("Decision Date:", allow_indent=True)
        )
        lower_court_rehearing_denied = self.normalize_date(
            self._td_value_by_label("Rehearing Denied:", allow_indent=True)
        )
        discretionary_court_decision = self.normalize_date(
            self._td_value_by_label(
                "Discretionary Court Decision Date:", allow_indent=True
            )
        )

        # Questions Presented
        questions_presented_label = self.tree.xpath(
            "//tr[td[1][starts-with(normalize-space(.), 'Questions Presented')]]//a[@href]"
        )
        questions_presented_val = (
            questions_presented_label[0].get("href")
            if questions_presented_label
            else None
        )

        return {
            "docket_number": docket_number,
            "capital_case": None,
            "date_filed": date_filed,
            "case_name": case_name,
            "links": links,
            "lower_court": lower_court or None,
            "lower_court_case_numbers_raw": lower_court_raw or None,
            "lower_court_case_numbers": lower_court_cleaned,
            "lower_court_decision_date": lower_court_decision_date,
            "lower_court_rehearing_denied_date": lower_court_rehearing_denied,
            "questions_presented": questions_presented_val or None,
            "discretionary_court_decision": discretionary_court_decision,
        }

    @staticmethod
    def _parse_description_html(td) -> str:
        """Parse the cell content up to the first <br>, excluding
        .documentlinks.

        :param td: <td> element with the text description.
        :return: The description_html.
        """
        parts = []
        if td is None:
            return ""

        if td.text:
            parts.append(td.text)

        for child in td:
            tag = getattr(child, "tag", "")
            if tag and tag.lower() == "br":
                break
            # If a documentlinks span appears before a <br>, stop there too.
            if "documentlinks" in (child.get("class") or ""):
                break

            parts.append(html.tostring(child, encoding="unicode"))
            # Include its tail too.
            if child.tail:
                parts.append(child.tail)

        return "".join(parts)

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
        :param attachment_path: XPath to select attachment anchors inside the
        description cell.
        :param table_layout: If parsing a table layout docket.
        :return: Dict with date_filed, description, description_html, attachments.
        """
        description_html = ""
        attachments: list[dict[str, Any]] = []
        document_number: Optional[int] = None

        if description_td is not None:
            # Select content up to first <br> and excluding .documentlinks;
            # fallback to whole cell.
            description_html = (
                self._parse_description_html(description_td).strip()
                or html.tostring(description_td, encoding="unicode").strip()
            )
            # Parse attachments.
            for a in description_td.xpath(attachment_path):
                href = a.get("href")
                if not href:
                    continue

                if document_number is None and "DocketPDF" in href:
                    match = re.search(self.DOC_NUM_RE, href)
                    if match:
                        document_number = int(match.group(1))

                if table_layout and href:
                    logger.error(
                        "Found a potential attachment in a table-layout docket. "
                        "This could be an opportunity to add support for it."
                    )

                short_desc = self._clean_whitespace(
                    (a.text or a.get("title") or "").strip()
                )
                attachments.append(
                    {
                        "description": short_desc or "Document",
                        "document_url": href,
                        "document_number": document_number,
                    }
                )

        cleaned = strip_bad_html_tags_insecure(description_html or "")
        description = self._clean_whitespace(cleaned.text_content())

        return {
            "date_filed": self.normalize_date(date_str),
            "document_number": document_number,
            "description": description,
            "description_html": description_html,
            "attachments": attachments,
        }

    @property
    def docket_entries(self) -> list[dict[str, Any]]:
        """Return docket entries from 'Proceedings and Orders'.

        :return: List of dicts with date_filed, description, description_html,
        attachments.
        """
        if self.tree is None:
            return []

        # Div-based layout
        entries: list[dict[str, Any]] = []
        rows = self.tree.xpath(
            "//div[@id='proceedings']//div[contains(@class,'card')]"
            "//table[contains(@class,'ProceedingItem')]//tr"
        )
        for tr in rows:
            date_td = tr.xpath("./td[contains(@class,'ProceedingDate')]")
            text_td = tr.xpath("./td[not(contains(@class,'ProceedingDate'))]")
            date_str = self._join_nodes_content(date_td)
            description_td = text_td[0] if text_td else None
            entries.append(
                self._build_docket_entry(
                    date_str=date_str,
                    description_td=description_td,
                    attachment_path=".//span[contains(@class,'documentlinks')]//a[contains(@class,'documentanchor')]",
                )
            )
        if entries:
            return entries

        # Table-based layout
        table = self.tree.xpath("//table[@id='proceedings']")
        if not table:
            return []

        entries = []
        for tr in table[0].xpath(".//tr[td]"):
            # omit proceedingheader header
            if tr.xpath(
                "./td[contains(concat(' ', normalize-space(@class), ' '), ' proceedingheader ')]"
            ):
                continue
            # omit borderbttm separator
            if tr.xpath(
                "./td[contains(concat(' ', normalize-space(@class), ' '), ' borderbttm ')]"
            ):
                continue

            # omit non entries cells.
            tds = tr.xpath("./td")
            if len(tds) < 2:
                continue

            date_td, text_td = tds[:2]
            date_str = self._clean_whitespace(date_td.text_content())

            # Table layout, any link in the cell is a potential attachment.
            entries.append(
                self._build_docket_entry(
                    date_str=date_str,
                    description_td=text_td,
                    attachment_path=".//a[@href]",
                    table_layout=True,
                )
            )

        return entries

    @property
    def parties(self) -> list[dict[str, Any]]:
        """Return parties grouped under Contacts (Petitioner/Respondent/Other).

        Tries the card-based layout first. If not found, tries the table-based layout.
        :return: List of dicts containing parties data.
        """
        if self.tree is None:
            return []

        parties = self._parties_from_cards()
        if parties:
            return parties

        return self._parties_from_contacts_table()

    def _parties_from_cards(self) -> list[dict[str, Any]]:
        """Parse parties from the Contacts card-based layout.

        :return: List of dicts containing parties data.
        """
        sections = [
            ("Attorneys for Petitioners", "Petitioner"),
            ("Attorneys for Respondents", "Respondent"),
            ("Other Attorneys", "Other"),
        ]

        parties: list[dict] = []

        for heading_text, type_key in sections:
            section_root = self._section_by_heading(heading_text)
            if section_root is None:
                continue

            names = section_root.xpath(
                ".//div[contains(@class,'ContactName')]"
            )
            contact_data = section_root.xpath(
                ".//div[contains(@class,'ContactData2')]"
            )

            attorneys_by_party = defaultdict(list)
            for i, name_div in enumerate(names):
                data_div = contact_data[i] if i < len(contact_data) else None
                attorney = self._build_attorney_from_contact(
                    name_div, data_div
                )
                # Normalize party_name
                party_name = ""
                if data_div is not None:
                    party_name_raw = data_div.xpath(
                        ".//span[contains(@class,'partyname')]/text()"
                    )
                    party_name = (
                        self._clean_whitespace("".join(party_name_raw)) or ""
                    )
                party_name = party_name.replace("Party name:", "").strip()
                attorneys_by_party[(type_key, party_name)].append(attorney)

            parties.extend(
                {"type": t, "name": n, "attorneys": attys}
                for (t, n), attys in attorneys_by_party.items()
            )
        return parties

    def _parties_from_contacts_table(self) -> list[dict[str, Any]]:
        """Parse parties from the table-based contacts layout.

        :return: List of dicts containing parties data.
        """
        table = next(iter(self.tree.xpath("//table[@id='Contacts']")), None)
        if table is None:
            return []

        parties_by_key: dict[tuple[str, str], list] = defaultdict(list)
        current_type = None
        rows = table.xpath(".//tr[td]")
        for i, tr in enumerate(rows):
            # omit section header
            if tr.xpath(
                "./td[contains(concat(' ', normalize-space(@class), ' '), ' ContactSubHeader ')]"
            ):
                header_text = self._clean_whitespace(
                    "".join(
                        tr.xpath(
                            ".//span[contains(@class,'tableheadertext')]/text()"
                        )
                    )
                )
                current_type = self._map_contacts_header_to_type(header_text)
                continue

            # Attorney row
            tds = tr.xpath("./td")
            if current_type and len(tds) == 3:
                name_td, addr_td, phone_td = tds
                name_text = self._clean_whitespace(
                    self._parse_description_html(name_td) or ""
                )
                full_name_cell = self._clean_whitespace(name_td.text_content())
                is_counsel_of_record = bool(
                    re.search(r"\bcounsel of record\b", full_name_cell, re.I)
                )

                contact_data = self._parse_contacts_table_address_cell(addr_td)
                title = contact_data.title
                address_lines = contact_data.address_lines
                city = contact_data.city
                state = contact_data.state
                zip_code = contact_data.zip_code
                email = contact_data.email
                phone = self._clean_whitespace(phone_td.text_content()) or None

                # Party row
                party_name = ""
                if i + 1 < len(rows):
                    next_tr = rows[i + 1]
                    if next_tr.xpath(
                        "./td[contains(concat(' ', normalize-space(@class), ' '), ' ContactParty ')]"
                        " | ./td[contains(normalize-space(string(.)), 'Party name:')]"
                    ):
                        raw_party = self._clean_whitespace(
                            next_tr.text_content()
                        )
                        party_name = re.sub(
                            r"^Party name:\s*", "", raw_party, flags=re.I
                        ).strip()

                # Build attorney
                attorney = {
                    "name": name_text or None,
                    "is_counsel_of_record": is_counsel_of_record,
                    "title": title,
                    "phone": phone,
                    "address": ", ".join(address_lines)
                    if address_lines
                    else None,
                    "city": city,
                    "state": state,
                    "zip": zip_code,
                    "email": email,
                }
                # Group parties by type-name
                parties_by_key[(current_type, party_name or "")].append(
                    attorney
                )

        return [
            {"type": party_type, "name": name, "attorneys": attorneys}
            for (party_type, name), attorneys in parties_by_key.items()
        ]

    @staticmethod
    def _map_contacts_header_to_type(header_text: str) -> Optional[str]:
        """Map table section headers to normalized types.

        :param header_text: Text to be mapped.
        :return: Normalized party type or None.
        """
        t = (header_text or "").strip().lower()
        if "petitioner" in t:
            return "Petitioner"
        if "respondent" in t:
            return "Respondent"
        if "other" in t:
            return "Other"
        return None

    def _append_clean_text(
        self, text: Optional[str], lines: list[str]
    ) -> None:
        """Clean the given text and append it to the list of lines if not empty."""
        cleaned = self._clean_whitespace(text)
        if cleaned:
            lines.append(cleaned)

    def _parse_address_title(self, lines) -> tuple[Optional[str], int]:
        """Extract the party title from address lines and determine where the address begins.

        :param lines: A list of text lines containing the party title and address.
        :return: A twp tuple where the first element is the concatenated title
        string and th index where the address starts.
        """
        title_parts = []
        start_add_idx = 0
        # Parse title.
        for j, ln in enumerate(lines):
            if self.ID_RE.match(ln):
                # Omit lines starting with # like #1098260
                continue
            if self.ADDRESS_NUMBER.search(ln):
                # Match the start of an address by looking for a street number.
                start_add_idx = j
                break
            title_parts.append(ln)

        title = ", ".join(title_parts) or None
        return title, start_add_idx

    def _parse_address_lines(self, lines, start_add_idx) -> ContactAddress:
        """Parse the address components starting from a given index.

        :param lines: A list of text lines containing the address data.
        :param start_add_idx: Index indicating where the address lines begin.
        :return: A ContactAddress object.
        """

        address_lines = (
            lines[start_add_idx:] if start_add_idx < len(lines) else []
        )

        # parse City/State/Zip
        city = state = zip_code = None
        if address_lines:
            last = address_lines[-1]
            if m := re.search(self.ADDRESS_RE, last):
                city, state, zip_code = (
                    m.group(1).strip(),
                    m.group(2),
                    m.group(3),
                )
                address_lines = address_lines[:-1]

        return ContactAddress(
            title=None,
            address_lines=address_lines,
            city=city,
            state=state,
            zip_code=zip_code,
            email=None,
        )

    def _parse_contacts_table_address_cell(
        self, td: HtmlElement
    ) -> ContactAddress:
        """Parse the address TD of the table layout into a ContactAddress object.

        :param td: The td element to parse the address from.
        :return: A ContactAddress object.
        """

        raw_lines: list[str] = []
        self._append_clean_text(td.text, raw_lines)
        for child in td:
            self._append_clean_text(child.text, raw_lines)
            self._append_clean_text(child.tail, raw_lines)

        lines = [
            ln for ln in (self._clean_whitespace(ln) for ln in raw_lines) if ln
        ]

        # Extract email line
        email = None
        for idx, ln in list(enumerate(lines)):
            if m := self.EMAIL_RE.search(ln):
                email = m.group(0)
                del lines[idx]
                break

        title, start_add_idx = self._parse_address_title(lines)
        partial_address = self._parse_address_lines(lines, start_add_idx)

        return ContactAddress(
            title=title,
            address_lines=partial_address.address_lines,
            city=partial_address.city,
            state=partial_address.state,
            zip_code=partial_address.zip_code,
            email=email,
        )

    def _section_by_heading(self, heading_text: str) -> Optional[HtmlElement]:
        """Return the "card-body" node for a given Contacts
        section heading.

        :param heading_text: The header text like "Attorneys for Petitioners".
        :return: The matching "card-body" node, or None if not found.
        """
        if self.tree is None:
            return None

        xpath_query = (
            "//div[@id='Contacts']//div[contains(@class,'card')]"
            f"[.//div[contains(@class,'card-heading') and normalize-space()='{heading_text}']]"
            "//div[contains(@class,'card-body')]"
        )

        return next(iter(self.tree.xpath(xpath_query)), None)

    def _build_attorney_from_contact(
        self, name_div: HtmlElement, data_div: Optional[HtmlElement]
    ) -> dict[str, Any]:
        """Build an attorney dict from ContactName/ContactData2 pair.

        :param name_div: ContactName div.
        :param data_div: ContactData2 div.
        :return: Attorney dict matching the JSON parser shape.
        """
        name_text = self._clean_whitespace(
            self._parse_description_html(name_div)
        )
        is_counsel_of_record = bool(
            name_div.xpath(
                ".//span[contains(@class,'ContactTitle')][contains(., 'Counsel of Record')]"
            )
        )

        title = address = city = state = zip_code = email = phone = None
        if data_div is not None:
            email = self._clean_whitespace(
                self._join_nodes_content(
                    data_div.xpath(".//span[contains(@class,'emailaddress')]")
                )
            )
            phone = self._clean_whitespace(
                self._join_nodes_content(
                    data_div.xpath(".//span[contains(@class,'phonenumber')]")
                )
            )
            phone = phone.replace("Ph:", "").strip() if phone else None

            address_span = data_div.xpath(
                ".//span[contains(@class,'address1')]"
            )
            if address_span:
                contact_data = self._parse_address_block(address_span[0])
                title = contact_data.title
                address_lines = contact_data.address_lines
                city = contact_data.city
                state = contact_data.state
                zip_code = contact_data.zip_code
                address = ", ".join(address_lines) if address_lines else None

        return {
            "name": name_text or None,
            "is_counsel_of_record": is_counsel_of_record,
            "title": title,
            "phone": phone,
            "address": address,
            "city": city,
            "state": state,
            "zip": zip_code,
            "email": email or None,
        }

    def _parse_address_block(self, node: HtmlElement) -> ContactAddress:
        """Parse the address block into title, address lines, city, state, zip.

        :param node: The HTML element (usually span.address1) to split by <br>.
        :return: A ContactAddress object.
        """

        raw_lines: list[str] = []
        self._append_clean_text(node.text, raw_lines)
        for child in node:
            self._append_clean_text(child.text, raw_lines)
            self._append_clean_text(child.tail, raw_lines)

        if len(raw_lines) >= 3:
            # If more than 3 lines. Title is the first one.
            title = raw_lines[0]
            address_lines = raw_lines[1:]
        else:
            # 0, 1, or 2 lines, there is no title
            title = None
            address_lines = raw_lines[:]

        # Extract city/state/zip from the last address line, if present
        city = state = zip_code = None
        if address_lines:
            last = address_lines[-1]
            m = re.search(r"([^,]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$", last)
            if m:
                city, state, zip_code = (
                    m.group(1).strip(),
                    m.group(2),
                    m.group(3),
                )
                address_lines = address_lines[:-1]

        return ContactAddress(
            title=title,
            address_lines=address_lines,
            city=city,
            state=state,
            zip_code=zip_code,
            email=None,
        )

    def _td_value_by_label(
        self, label: str, allow_indent: bool = False
    ) -> Optional[str]:
        """Fetch the value from the docketinfo table whose first TD label matches.

        :param label: The label text in the first TD.
        :param allow_indent: True to allow labels with leading indentation.
        :return: Cleaned string value or None.
        """
        if self.tree is None:
            return None

        if allow_indent:
            # Parse labels like "&nbsp;&nbsp;&nbsp;Case Numbers:"
            target_label = (
                f"//table[@id='docketinfo']//tr[td[1]/span[normalize-space(translate(text(), '\u00a0',' '))='{label}']]"
                "/td[2]//span"
            )
        else:
            target_label = f"//table[@id='docketinfo']//tr[td[1]/span[normalize-space(text())='{label}']]/td[2]//span"

        return self._clean_whitespace(
            self._join_nodes_content(self.tree.xpath(target_label))
        )

    @staticmethod
    def _clean_whitespace(text: Optional[str]) -> str:
        """Collapse whitespace to single spaces.

        :param text: Raw text.
        :return: Normalized text to a single-line.
        """
        return "" if not text else re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _join_nodes_content(nodes: list[HtmlElement]) -> str:
        """Concatenate the text content of multiple HTML nodes.

        :param nodes: List of lxml HtmlElement objects.
        :return: Combined and cleaned text content.
        """
        return "".join(
            node.text_content() for node in nodes if node is not None
        ).strip()


def _main():
    """Parse a local HTML file and pretty-print normalized data.

    :return: None
    """
    import pprint
    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python -m juriscraper.scotus_docket_report_html <filepath>"
        )
        sys.exit(1)

    parser = SCOTUSDocketReportHTML()
    with open(sys.argv[1], encoding="utf-8") as f:
        parser._parse_text(f.read())
    pprint.pprint(parser.data, indent=2)


if __name__ == "__main__":
    _main()
