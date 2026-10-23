import json
import pprint
import re
import sys
from collections import defaultdict
from collections.abc import Hashable
from typing import Any

from juriscraper.lib.html_utils import strip_bad_html_tags_insecure
from juriscraper.lib.log_tools import make_default_logger

from ._scotus_docket_report_parsing import (
    DOC_NUM_RE,
    clean_lower_court_cases,
    normalize_date,
)

logger = make_default_logger()


class SCOTUSDocketReport:
    """Parse SCOTUS docket JSON"""

    SCOTUS_BASE_URL = "https://www.supremecourt.gov"

    def __init__(self, court_id: str = "scotus"):
        self._scotus_json: dict[Hashable, Any] | None = None

    @property
    def data(self) -> dict[str, Any]:
        """Get all the data back from this endpoint."""
        metadata = self.metadata or {}
        if not metadata:
            return {}
        case_name = metadata.get("case_name")
        if not case_name:
            logger.error("Failed to extract SCOTUS docket number.")
            return {}
        docket_number = metadata.get("docket_number")
        if not docket_number:
            logger.error("Failed to extract SCOTUS docket number.")
            return {}
        return {
            **metadata,
            "parties": self.parties,
            "docket_entries": self.docket_entries,
        }

    def _parse_text(self, text: str) -> None:
        """Load and store the JSON object.

        :param text: The raw JSON unicode object
        :return: None
        """
        json_object = json.loads(text or "{}")
        # Perform minimal validation to guarantee dictionary type.
        if not isinstance(json_object, dict):
            raise ValueError("`text` is not a JSON object.")
        self._scotus_json = json_object

    @property
    def metadata(self) -> dict[str, Any]:
        """Return normalized docket metadata.
        That function then supplements it with parties and docket entries.

        :return: Dict with case_number, docket_date, case_title, lower_court, etc.
        """
        if not self._scotus_json:
            logger.error("_parse_text() must be called first.")
            return {}

        scotus_data = self._scotus_json
        docket_number = (scotus_data.get("CaseNumber", "")).strip()
        docket_number = (
            docket_number.replace("*** CAPITAL CASE ***", "").strip()
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
        questions_presented_raw = scotus_data.get("QPLink", "")
        questions_presented = re.sub(
            r"^\.\.", self.SCOTUS_BASE_URL, questions_presented_raw
        )

        return {
            "docket_number": docket_number,
            "capital_case": scotus_data.get("bCapitalCase"),
            "date_filed": normalize_date(docket_date),
            "case_name": case_name.strip() if case_name else "",
            "links": links,
            "lower_court": lower_court.strip() if lower_court else None,
            "lower_court_case_numbers_raw": lower_court_case_numbers_raw.strip()
            if lower_court_case_numbers_raw
            else None,
            "lower_court_case_numbers": clean_lower_court_cases(
                lower_court_case_numbers_raw
            )
            if lower_court_case_numbers_raw
            else None,
            "lower_court_decision_date": normalize_date(
                lower_court_decision_date
            ),
            "lower_court_rehearing_denied_date": normalize_date(
                lower_court_rehearing_denied_date
            ),
            "questions_presented": questions_presented or None,
            "discretionary_court_decision": normalize_date(
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
                    "description":"Main Document"
                 }
              ],
              "date_filed":"2024-07-30",
              "description":"Application (24A100) granted by Justice Kagan extending the time to file until October 5, 2024.",
              "description_html":"Application (24A100) <a href=#>granted</a> by Justice Kagan extending the time to file until October 5, 2024."
           }
        ]

        :return: List of docket entry dicts
        """
        if not self._scotus_json:
            logger.error("_parse_text() must be called first.")
            return []

        entries = []
        for row in self._scotus_json.get("ProceedingsandOrder", []):
            links = row.get("Links", [])
            document_number = None
            if links and (
                match := re.search(
                    DOC_NUM_RE, links[0].get("DocumentUrl") or ""
                )
            ):
                document_number = int(match.group(1))
            attachments = [
                {
                    "description": link.get("Description", "").strip(),
                    "document_url": link.get("DocumentUrl"),
                    "document_number": document_number,
                }
                for link in links
            ]

            description_html = row.get("Text", "")
            description = strip_bad_html_tags_insecure(description_html)
            de = {
                "date_filed": normalize_date(row.get("Date")),
                "document_number": document_number,
                "description": description.text_content(),
                "description_html": description_html,
                "attachments": attachments,
            }
            entries.append(de)
        return entries

    @staticmethod
    def _build_attorney(att: dict[str, Any]) -> dict[str, Any]:
        """Build a normalized attorney dictionary from a raw SCOTUS JSON record.

        :param att: dictionary containing attorney information from the SCOTUS JSON.
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
        if not self._scotus_json:
            logger.error("_parse_text() must be called first.")
            return []

        type_parties = self._scotus_json.get(type_key, [])
        if not type_parties:
            return []

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for party in type_parties:
            party_name = party.get("PartyName", "").strip()
            grouped[party_name].append(self._build_attorney(party))

        return [
            {
                "type": type_key,
                "name": party_name,
                "attorneys": attorneys,
            }
            for party_name, attorneys in grouped.items()
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
