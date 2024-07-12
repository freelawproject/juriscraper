import json
import pprint
import sys
import unicodedata
from typing import Dict

from ..lib.html_utils import strip_bad_html_tags_insecure
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import convert_date_string
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
        self._acms_json = {}
        try:
            attachment_json = json.loads(text)
            self.check_validity(attachment_json)
            if self.is_valid:
                self._acms_json = attachment_json
        except json.JSONDecodeError:
            self.is_valid = False

    def _clean_attachment_description(self, text: str) -> str:
        """
        This function extracts the description from a string with a specific
        format.

        Based on our analysis of ACMS examples, a valid attachment entry
        description string has the following structure:
            - Docket number, entry number, and attachment number (separated
              by hyphens)
            - A description of the entry
            - The description followed by a period (".") and the file format
              (e.g., ".pdf", ".txt")

        Args:
            text: The string containing the information.

        Returns:
            The extracted description as a string.
        """
        # Split the string on delimiters
        parts = text.split(" - ")

        # Validates if the string follows the expected format for ACMS
        # attachment entries.
        if len(parts) != 3:
            return text

        # Extract description before format extension
        return parts[-1].split(".")[0]

    def check_validity(self, parsed_json: dict) -> None:
        """Place sanity checks here to make sure that the returned json is
        valid and not an error page or some other kind of problem.

        Set self.is_valid flag to True or False
        """
        if not all(
            [
                x in parsed_json
                for x in ["caseDetails", "docketEntry", "docketEntryDocuments"]
            ]
        ):
            self.is_valid = False
            return
        self.is_valid = True

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
        if not self.is_valid:
            return {}

        case_details = self._acms_json["caseDetails"]
        docket_entry = self._acms_json["docketEntry"]
        de_text = strip_bad_html_tags_insecure(docket_entry["docketEntryText"])
        result = {
            "pacer_doc_id": docket_entry["docketEntryId"],
            "pacer_case_id": case_details["caseId"],
            "entry_number": docket_entry["entryNumber"],
            "description": unicodedata.normalize(
                "NFKD", de_text.text_content()
            ),
            "date_filed": convert_date_string(docket_entry["createdOn"]),
            "date_end": convert_date_string(docket_entry["endDate"]),
            "attachments": [],
        }

        for row in self._acms_json["docketEntryDocuments"]:
            result["attachments"].append(
                {
                    "attachment_number": int(row["documentNumber"]),
                    "description": self._clean_attachment_description(
                        row["name"]
                    ),
                    "page_count": row["billablePages"],
                    "pacer_doc_id": docket_entry["docketEntryId"],
                    "acms_document_guid": row["docketDocumentDetailsId"],
                    "cost": row["cost"],
                    "date_filed": convert_date_string(row["createdOn"]),
                    "permission": row["documentPermission"],
                    "file_size": row["fileSize"],
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
