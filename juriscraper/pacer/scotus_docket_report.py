import json
import pprint
import re
import sys
from datetime import datetime
from typing import Any, Optional

from juriscraper.lib.html_utils import strip_bad_html_tags_insecure


class SCOTUSDocketReport:
    """Parse SCOTUS docket JSON (TODO:HTML/HTM variant)."""

    DATE_FORMATS = (
        "%B %d, %Y",  # July 3, 2024
        "%b %d %Y",  # Jul 03 2024
        "%b %d, %Y",  # Jul 03, 2024
        "%m/%d/%Y",  # 08/16/2024
    )

    LOWER_COURT_PATTERNS = {
        "slash_same_prefix": re.compile(r"^\d+-[A-Za-z]*-?\d+(/\d+)+$"),
        "sep_inherited_prefix": re.compile(r"^\d+-\d+([;/,-]-\d+)+$"),
        "neg_prefix_numbers": re.compile(r"^\d+-\d+(,-\d+)*,-?$"),
        "comma_correct_prefix": re.compile(
            r"^(\d+-[A-Za-z]+, )*\d+-[A-Za-z]+$"
        ),
        "slash_shared_prefix": re.compile(r"^\d+-\d+(/\d+)+$"),
        "special_formats": [
            re.compile(r"^(CR|CA)-\d+-\d+$"),
            re.compile(r"^\d+-\d+-\d+-[A-Za-z]+$"),
        ],
        "neg_prefix_list": re.compile(r"^\d+-\d+(,-\d+)+$"),
    }

    def __init__(self, court_id: str = "scotus"):
        self._scotus_json = None

    @property
    def data(self) -> dict:
        """Get all the data back from this endpoint."""
        return {
            **(self.metadata or {}),
            "parties": self.parties,
            "docket_entries": self.docket_entries,
        }

    def _parse_text(self, text: str) -> None:
        """Load and store the JSON object.

        :param text: The raw JSON unicode object
        :return: None
        """
        self._scotus_json = json.loads(text or "{}")

    @property
    def metadata(self) -> dict[str, Any]:
        """Return normalized docket metadata.
        That function then supplements it with parties and docket entries.

        :return: Dict with case_number, docket_date, case_title, lower_court, etc.
        """

        scotus_data = self._scotus_json
        docket_number = (scotus_data.get("CaseNumber") or "").strip()
        docket_number = (
            docket_number.replace(" *** CAPITAL CASE ***", "")
            if docket_number
            else None
        )
        docket_date = scotus_data.get("DocketedDate", "")
        respondent_title = scotus_data.get("RespondentTitle", "")
        petitioner_title = scotus_data.get("PetitionerTitle", "")
        case_name = (
            f"{petitioner_title} v. {respondent_title}"
            if respondent_title
            else petitioner_title
        )
        lower_court = scotus_data.get("LowerCourt", "")
        lower_court_case_numbers_raw = scotus_data.get(
            "LowerCourtCaseNumbers", ""
        )
        lower_court_decision_date = scotus_data.get("LowerCourtDecision", "")
        lower_court_rehearing_denied_date = scotus_data.get(
            "LowerCourtRehearingDenied", ""
        )
        links = scotus_data.get("Links", "").replace("Linked with", "").strip()
        return {
            "docket_number": docket_number,
            "capital_case": scotus_data.get("bCapitalCase"),
            "date_filed": self.normalize_date(docket_date),
            "case_name": case_name.strip() if case_name else "",
            "links": links,
            "lower_court": lower_court.strip() if lower_court else None,
            "lower_court_case_numbers_raw": lower_court_case_numbers_raw.strip()
            if lower_court_case_numbers_raw
            else None,
            "lower_court_case_numbers": self.clean_lower_court_cases(
                lower_court_case_numbers_raw
            )
            if lower_court_case_numbers_raw
            else None,
            "lower_court_decision_date": self.normalize_date(
                lower_court_decision_date
            ),
            "lower_court_rehearing_denied_date": self.normalize_date(
                lower_court_rehearing_denied_date
            ),
            "discretionary_court_decision": self.normalize_date(
                scotus_data.get("DiscretionaryCourtDecision", "")
            ),
        }

    @property
    def docket_entries(self) -> list[dict[str, Any]]:
        """Return a dictionary of docket entries from ProceedingsandOrder

        [
           {
              "attachments":[
                 {
                    "document_url":"http://www.supremecourt.gov/DocketPDF/24/24A100/319653/20240723152722701_Johnson%20cert%20extension.pdf",
                    "short_description":"Main Document"
                 }
              ],
              "date_filed":"2024-07-30",
              "description":"Application (24A100) granted by Justice Kagan extending the time to file until October 5, 2024.",
              "description_html":"Application (24A100) <a href=#>granted</a> by Justice Kagan extending the time to file until October 5, 2024."
           }
        ]

        :return: List of docket entry dicts
        """
        entries = []
        for row in self._scotus_json.get("ProceedingsandOrder", []):
            links = row.get("Links") or []
            attachments = [
                {
                    "short_description": link.get("Description", "").strip(),
                    "document_url": link.get("DocumentUrl"),
                }
                for link in links
            ] or []

            description_html = row.get("Text", "")
            description = strip_bad_html_tags_insecure(description_html)
            de = {
                "date_filed": self.normalize_date(row.get("Date")),
                "description": description.text_content(),
                "description_html": description_html,
                "attachments": attachments,
            }
            entries.append(de)
        return entries

    @staticmethod
    def _build_attorney(att: dict[str, Any]) -> dict[str, Any]:
        """Build a normalized attorney dictionary from a raw SCOTUS JSON record.

        :param a: dictionary containing attorney information from the SCOTUS JSON.
        :return: Dictionary with normalized attorney fields.
        """

        return {
            "name": att.get("Attorney"),
            "is_counsel_of_record": bool(att.get("IsCounselofRecord")),
            "title": att.get("Title"),
            "phone": att.get("Phone"),
            "address": att.get("Address", "").strip(),
            "city": att.get("City"),
            "state": att.get("State"),
            "zip": att.get("Zip"),
            "email": att.get("Email"),
        }

    def _build_parties_for_type(self, type_key: str) -> list[dict[str, Any]]:
        """Group attorneys by party name for a party type.

        Preserves the order of first appearance of each party name and assigns all
        attorneys with the same `PartyName` to that party.

        :param type_key: The top-level SCOTUS JSON key for the party type
        (e.g., "Petitioner", "Respondent", "Other").
        :return: A list of dictionaries, each representing a party, with:
            - type: Party type (matches `type_key`)
            - name: Party name (from `PartyName`)
            - attorneys: List of attorney dictionaries.
        """

        type_parties = self._scotus_json.get(type_key) or []
        if not type_parties:
            return []

        # Keep insertion order of first appearance of each PartyName
        grouped: dict[str, list[dict[str, Any]]] = {}
        order = []
        for party in type_parties:
            party_name = party.get("PartyName", "").strip()
            if party_name not in grouped:
                grouped[party_name] = []
                order.append(party_name)
            grouped[party_name].append(self._build_attorney(party))

        return [
            {
                "type": type_key,
                "name": party_name,
                "attorneys": grouped[party_name],
            }
            for party_name in order
        ]

    @property
    def parties(self) -> list[dict[str, Any]]:
        """Return parties with their attorneys from Petitioner/Respondent arrays.

            [
               {
                  "attorneys":[
                     {
                        "address":"...",
                        "city":"Seattle",
                        "email":"user@email.org",
                        "is_counsel_of_record":true,
                        "name":"...",
                        "phone":"...",
                        "state":"WA",
                        "title":"...",
                        "zip":"98101"
                     }
                  ],
                  "name":"...",
                  "type":"Petitioner"
               }
            ]

        :return: List of parties dicts.
        """
        parties = []
        parties.extend(self._build_parties_for_type("Petitioner"))
        parties.extend(self._build_parties_for_type("Respondent"))
        parties.extend(self._build_parties_for_type("Other"))
        return parties

    @classmethod
    def normalize_date(
        cls, date_str: Optional[str]
    ) -> Optional[datetime.date]:
        """Convert a date string to YYYY-MM-DD using common SCOTUS formats.

        :param date_str: Raw date string (e.g., "July 3, 2024", "Jul 03 2024", "08/16/2024")
        :return: A date python object or None
        """
        if not date_str:
            return None
        s = date_str.strip()
        for date_format in cls.DATE_FORMATS:
            try:
                return datetime.strptime(s, date_format).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _apply_prefix(prefix: str, parts: list[str]) -> list[str]:
        """Prepend prefix to numeric parts."""
        return [
            f"{prefix}{p.strip()}" if p.strip().isdigit() else p.strip()
            for p in parts
        ]

    @staticmethod
    def _clean_parts(parts: list[str]) -> list[str]:
        """Clean lower court numbers

        :param parts: list of strings
        :return: list of cleaned lower court numbers
        """
        return [p.strip() for p in parts]

    def clean_lower_court_cases(self, raw_text: str) -> list[str]:
        """Clean and normalize lower court case numbers from various formats.

        :param raw_text: Raw text to be cleaned.
        :return: A list of lower court case numbers.
        """
        raw_text = raw_text.replace("(", "").replace(")", "").strip()

        # Case 1: Slash-separated numbers with same prefix
        if self.LOWER_COURT_PATTERNS["slash_same_prefix"].match(raw_text):
            parts = raw_text.split("/")
            prefix_match = re.match(r"(.*-)(\d+)$", parts[0])
            if not prefix_match:
                return raw_text.split(",")
            prefix = prefix_match.group(1)
            return self._clean_parts(
                self._apply_prefix(prefix, [p.lstrip("-") for p in parts])
            )

        # Case 2: Various separators with inherited prefixes: "98-4033;-4214;-4246"
        if self.LOWER_COURT_PATTERNS["sep_inherited_prefix"].match(raw_text):
            parts = re.split(r"[;/,-]", raw_text)
            prefix = parts[0].split("-")[0]
            return self._clean_parts(
                [
                    f"{prefix}-{p.strip('-')}"
                    for p in parts
                    if p.strip("-") != prefix
                ]
            )

        # Case 3: Negative prefix-separated numbers: "99-1845,-1846,-1847,-197" or "98-60240,-60454,-60467,-""
        if self.LOWER_COURT_PATTERNS["neg_prefix_numbers"].match(raw_text):
            prefix_match = re.match(r"(\d+-)(\d+)", raw_text)
            if not prefix_match:
                return raw_text.split(",")
            prefix = prefix_match.group(1)
            numbers = [prefix_match.group(2)] + raw_text[
                len(prefix_match.group(0)) :
            ].split(",")
            return self._clean_parts(
                [f"{prefix}{n.strip('-')}" for n in numbers if n.strip("-")]
            )

        # Case 4: Comma-separated items with prefixes already correct: "33094-CW, 33095-CW"
        if self.LOWER_COURT_PATTERNS["comma_correct_prefix"].match(raw_text):
            return raw_text.split(",")

        # Case 5: Mixed slash-separated values with a shared prefix: "98-16950/17044/17137"
        if self.LOWER_COURT_PATTERNS["slash_shared_prefix"].match(raw_text):
            prefix = raw_text.split("-")[0]
            parts = raw_text.split("/")
            return self._clean_parts(
                [f"{prefix}-{p.split('-')[-1]}" for p in parts]
            )

        # Case 6: Ampersand-separated with prefixes or 'See also'-separated with prefixes: "95-56639 & 96-55194" or "95-56639 See also 96-55194"
        if "&" in raw_text:
            return raw_text.replace(" & ", ", ").split(",")
        if "See also" in raw_text:
            return raw_text.replace(" See also ", ", ").split(",")

        # Case 7: Preserve specific formats: "CR-99-1140", "1998-CA-0022039-MR"
        if any(
            p.match(raw_text)
            for p in self.LOWER_COURT_PATTERNS["special_formats"]
        ):
            return raw_text.split(",")

        # Case 8: Range expansion: "97-1715/98-1111 to 1115" or "97-1715/1111 to 1115"
        if re.search(r"\d+/\d+(-\d+)? to \d+", raw_text):
            parts = raw_text.split("/")
            cleaned = [parts[0]]
            range_part = parts[1]

            if " to " in range_part:
                start, end = range_part.split(" to ")
                if "-" in start:
                    sprefix, snum = re.match(r"(\d+)-(\d+)", start).groups()
                    cleaned.append(f"{sprefix}-{snum}")
                    end_num = int(re.match(r"(\d+-)?(\d+)", end).groups()[-1])
                    cleaned.extend(
                        f"{sprefix}-{i}"
                        for i in range(int(snum) + 1, end_num + 1)
                    )
                else:
                    prefix = parts[0].split("-")[0]
                    s, e = map(int, range_part.split(" to "))
                    cleaned.extend(f"{prefix}-{i}" for i in range(s, e + 1))
            else:
                cleaned.append(
                    f"{parts[0].split('-')[0]}-{range_part.strip()}"
                )

            return self._clean_parts(cleaned)

        # Case 9: Various separators with inherited prefixes: "98-4033;-4214;-4246"
        if self.LOWER_COURT_PATTERNS["sep_inherited_prefix"].match(raw_text):
            parts = re.split(r"[;/,-]", raw_text)
            prefix = parts[0].split("-")[0]
            return self._clean_parts(
                [f"{prefix}-{p.strip('-')}" for p in parts]
            )

        # Case 10: Negative prefix-separated numbers: "99-1845,-1846,-1847,-197"
        if self.LOWER_COURT_PATTERNS["neg_prefix_list"].match(raw_text):
            prefix = raw_text.split("-")[0]
            return self._clean_parts(
                [f"{prefix}-{n.strip('-')}" for n in raw_text.split(",")]
            )

        # Default cleanup for other separators
        return self._clean_parts(re.sub(r"[;&\n]", ",", raw_text).split(","))


def _main():
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.scotus_docket_report <filepath>")
        print("Please provide a path to a JSON file to parse.")
        sys.exit(1)

    report = SCOTUSDocketReport()
    filepath = sys.argv[1]
    print(f"Parsing JSON file at {filepath}")
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
