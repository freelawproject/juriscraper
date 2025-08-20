import re
from typing import Any, Optional

from lxml import html
from lxml.html import HtmlElement

from juriscraper.lib.html_utils import clean_html, strip_bad_html_tags_insecure
from juriscraper.lib.string_utils import clean_string, harmonize
from juriscraper.pacer import SCOTUSDocketReport


class SCOTUSDocketReportHTML(SCOTUSDocketReport):
    """Parse SCOTUS docket HTML."""

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
            m = re.search(r"No\.\s*([^\s<]+)", docket_title_text)
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

        links = (self._td_value_by_label("Linked with:") or "").strip()

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
            "discretionary_court_decision": None,
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

    @property
    def docket_entries(self) -> list[dict[str, Any]]:
        """Return docket entries from 'Proceedings and Orders'.

        :return: List of dicts with date_filed, description, description_html,
        attachments.
        """

        if self.tree is None:
            return []

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

            description_html = ""
            attachments = []
            if description_td is not None:
                # Only the content before <br> and exclude .documentlinks
                description_html = self._parse_description_html(
                    description_td
                ).strip()
                # Extract attachments from the full td cell
                for a in description_td.xpath(
                    ".//span[contains(@class,'documentlinks')]//a[contains(@class,'documentanchor')]"
                ):
                    attachments.append(
                        {
                            "short_description": self._clean_whitespace(
                                (a.text or "").strip()
                            ),
                            "document_url": a.get("href"),
                        }
                    )

            # Clean text description
            description_cleaned = strip_bad_html_tags_insecure(
                description_html or ""
            )
            description = self._clean_whitespace(
                description_cleaned.text_content()
            )
            entries.append(
                {
                    "date_filed": self.normalize_date(date_str),
                    "description": description,
                    "description_html": description_html,
                    "attachments": attachments,
                }
            )
        return entries

    @property
    def parties(self) -> list[dict[str, Any]]:
        """Return parties grouped under Contacts (Petitioner/Respondent/Other).

        :return: List of party dicts, each with name party name and attorneys list.
        """
        if self.tree is None:
            return []

        sections = [
            ("Attorneys for Petitioners", "Petitioner"),
            ("Attorneys for Respondents", "Respondent"),
            ("Other Attorneys", "Other"),
        ]

        parties = []
        for heading_text, type_key in sections:
            section_root = self._section_by_heading(heading_text)
            if section_root is None:
                continue

            names = section_root.xpath(
                ".//div[contains(@class,'ContactName')]"
            )
            datas = section_root.xpath(
                ".//div[contains(@class,'ContactData2')]"
            )

            for i, name_div in enumerate(names):
                data_div = datas[i] if i < len(datas) else None
                attorney = self._build_attorney_from_contact(
                    name_div, data_div
                )

                # Group attorneys by "party_name"
                party_name = None
                if data_div is not None:
                    pn = data_div.xpath(
                        ".//span[contains(@class,'partyname')]/text()"
                    )
                    party_name = self._clean_whitespace("".join(pn)) or None

                existing = next(
                    (
                        p
                        for p in parties
                        if p["type"] == type_key
                        and p["name"] == (party_name or "")
                    ),
                    None,
                )
                if existing:
                    existing["attorneys"].append(attorney)
                else:
                    parties.append(
                        {
                            "type": type_key,
                            "name": party_name.replace(
                                "Party name:", ""
                            ).strip()
                            or "",
                            "attorneys": [attorney],
                        }
                    )
        return parties

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
            xpath_expr = (
                f"//table[@id='docketinfo']//tr[td[1]/span[normalize-space(translate(text(), '\u00a0',' '))='{label}']]"
                "/td[2]//span"
            )
        else:
            xpath_expr = f"//table[@id='docketinfo']//tr[td[1]/span[normalize-space(text())='{label}']]/td[2]//span"

        return self._clean_whitespace(
            self._join_nodes_content(self.tree.xpath(xpath_expr))
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

    def _section_by_heading(self, heading_text: str) -> Optional[HtmlElement]:
        """Return the <div class="card-body"> for a given Contacts section heading.

        :param heading_text: The header text e.g. "Attorneys for Petitioners".
        :return: The matching <div class="card-body"> node, or None if not found.
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
                title, addr_lines, city, state, zip_code = (
                    self._parse_address_block(address_span[0])
                )
                address = ", ".join(addr_lines) if addr_lines else None

        return {
            "name": name_text or None,
            "is_counsel_of_record": is_counsel_of_record,
            "title": title,
            "phone": phone,
            "address": address,
            "city": city,
            "state": state,
            "zip": zip_code,
            "email": email,
        }

    def _parse_address_block(
        self, node: HtmlElement
    ) -> tuple[
        Optional[str], list[str], Optional[str], Optional[str], Optional[str]
    ]:
        """Parse the address block into title, address lines, city, state, zip.

        :param node: The HTML element to split by <br>.
        :return: A tuple: title, address_lines, city, state, zip
        """

        def add_line(s: Optional[str], acc: list[str]) -> None:
            s = self._clean_whitespace(s)  # or _normalize_ws
            if s:
                acc.append(s)

        lines = []
        add_line(node.text, lines)
        for child in node:
            add_line(child.text, lines)
            add_line(child.tail, lines)

        title = lines[0] if lines else None
        address_lines = lines[1:] if len(lines) > 1 else []
        city = state = zip_code = None
        if address_lines:
            last = address_lines[-1]
            matched_address = re.search(
                r"([^,]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$", last
            )
            if matched_address:
                city, state, zip_code = (
                    matched_address.group(1).strip(),
                    matched_address.group(2),
                    matched_address.group(3),
                )
                address_lines = address_lines[:-1]

        return title, address_lines, city, state, zip_code


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
