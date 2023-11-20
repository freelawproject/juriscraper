import json
import pprint
import sys
from typing import Dict

from ..lib.log_tools import make_default_logger
from .reports import BaseReport

logger = make_default_logger()


class ACMSAttachmentPage(BaseReport):
    """Parse ACMS attachment pages' JSON."""

    def __init__(self, court_id, pacer_session=None):
        super().__init__(court_id, pacer_session)

    def _parse_text(self, text):
        """Store the ACMS JSON

        This does not, in fact, actually *parse* the data, it
        stores it for subsequent parsing, which happens in
        data().

        :param text: A unicode object
        :return: None
        """
        self._acms_json = json.loads(text)

    @property
    def data(self) -> Dict:
        """Extract relevant information from the JSON payload
        provided by the extension.

        :return: a dict containing the following fields:
            - pacer_doc_id: The id of the main document.
            - pacer_case_id: The pacer case id for this case.
            - entry_number - The value of the row we came from.

            - attachments: A list of attached items with the following fields:
                - attachment_number: The attachment number.
                - description: A description of the item.
                - page_count: The number of pages for the attachment.
                - pacer_doc_id: The pacer doc id for the attachment (a str).
                - acms_document_guid: The GUID of the document in ACMS.
        """
        case_details = self._acms_json["caseDetails"]
        docket_entry = self._acms_json["docketEntry"]
        result = {
            "pacer_doc_id": docket_entry["docketEntryId"],
            "pacer_case_id": case_details["caseId"],
            "entry_number": docket_entry["entryNumber"],
            "attachments": [],
        }

        for row in self._acms_json["docketEntryDocuments"]:
            result["attachments"].append(
                {
                    "attachment_number": int(row["documentNumber"]),
                    "description": row["name"],
                    "page_count": row["billablePages"],
                    "pacer_doc_id": docket_entry["docketEntryId"],
                    "acms_document_guid": row["docketDocumentDetailsId"],
                }
            )

        return result


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python -m juriscraper.pacer.acms_attachment_page filepath"
        )
        print("Please provide a path to a file to parse.")
        sys.exit(1)
    # Court ID is only needed for querying.
    report = ACMSAttachmentPage("cand")
    filepath = sys.argv[1]
    print(f"Parsing JSON file at {filepath}")
    with open(filepath) as f:
        text = f.read()
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    main()
