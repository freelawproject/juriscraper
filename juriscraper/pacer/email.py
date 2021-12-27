import re
from datetime import date
from typing import Dict, List, Optional, Union

from ..lib.string_utils import clean_string, convert_date_string, harmonize
from .docket_report import BaseDocketReport
from .reports import BaseReport
from .utils import (
    get_pacer_case_id_from_doc1_url,
    get_pacer_doc_id_from_doc1_url,
    get_pacer_magic_num_from_doc1_url,
    get_pacer_seq_no_from_doc1_url,
)


class NotificationEmail(BaseDocketReport, BaseReport):
    """A BaseDocketReport for parsing PACER notification email parsing"""

    def __init__(self, court_id):
        self.court_id = court_id
        super().__init__(court_id)

    @property
    def data(self):
        base = {
            "court_id": self.court_id,
        }
        parsed = {}
        if self.tree is not None:
            parsed = {
                "case_name": self._get_case_name(),
                "docket_number": self._get_docket_number(),
                "date_filed": self._get_date_filed(),
                "docket_entries": self._get_docket_entries(),
                "email_recipients": self._get_email_recipients(),
            }

        return {**base, **parsed}

    def _sibling_path(self, label):
        """Gets the path string for the sibling of a label cell (td)

        Many data attributes are presented in the format of key: value in table syntax
        this is a good way to get the next element over from a label

        :param label: The cell label
        :returns: The Xpath to the next cell
        """
        return f'//td[contains(., "{label}:")]/following-sibling::td[1]'

    def _get_case_name(self) -> str:
        """Gets a cleaned case name from the email text

        :returns: Case name, cleaned and harmonized
        """
        path = self._sibling_path("Case Name")
        case_name = self._xpath_text_0(self.tree, path)
        if not case_name:
            case_name = self._xpath_text_0(self.tree, f"{path}/p")
            if not case_name:
                case_name = "Unknown Case Title"
        return clean_string(harmonize(case_name))

    def _get_docket_number(self) -> str:
        """Gets a docket number from the email text

        :returns: Docket number, parsed
        """
        path = self._sibling_path("Case Number")
        docket_number = self._parse_docket_number_strs(
            self.tree.xpath(f"{path}/a/text()")
        )
        if not docket_number:
            docket_number = self._parse_docket_number_strs(
                self.tree.xpath(f"{path}/p/a/text()")
            )
        return docket_number

    def _get_date_filed(self) -> date:
        """Gets the filing date from the email text

        :returns: Date filed as date object
        """
        date_filed = re.search(
            r"filed\son\s([\d|\/]*)",
            clean_string(self.tree.text_content()),
            flags=re.IGNORECASE,
        )
        return convert_date_string(
            date_filed[0].lower().replace("filed on ", "")
        )

    def _get_document_number(self) -> str:
        """Gets the specific document number the notification is referring to

        :returns: Document number, cleaned
        """
        path = self._sibling_path("Document Number")
        text = self.tree.xpath(path)[0].text_content()
        words = re.split(r"\(|\s", clean_string(text))
        return words[0]

    def _get_doc1_anchor(self) -> str:
        """Safely retrieves the anchor tag for the document

        :returns: Anchor tag, if it's found
        """
        try:
            path = f"{self._sibling_path('Document Number')}//a"
            return self.tree.xpath(path)[0]
        except IndexError:
            return None

    def _get_description(self):
        """Gets the docket text

        :returns: Cleaned docket text
        """
        path = '//strong[contains(., "Docket Text:")]/following-sibling::'
        node = self.tree.xpath(f"{path}font[1]/b/text()")
        if len(node):
            return clean_string(node[0])

        node = self.tree.xpath(f"{path}b[1]/span/text()")
        if len(node):
            return clean_string(node[0])

        return None

    def _get_docket_entries(
        self,
    ) -> List[Dict[str, Optional[Union[str, date]]]]:
        """Gets the full list of docket entries with document and sequence numbers

        :returns: List of docket entry dictionaries
        """
        description = self._get_description()
        if description is not None:
            anchor = self._get_doc1_anchor()
            document_url = (
                anchor.xpath("./@href")[0] if anchor is not None else None
            )
            entries = [
                {
                    "date_filed": self._get_date_filed(),
                    "description": description,
                    "document_url": document_url,
                    "document_number": self._get_document_number(),
                    "pacer_doc_id": None,
                    "pacer_case_id": None,
                    "pacer_seq_no": None,
                    "pacer_magic_num": None,
                }
            ]
            if document_url is not None:
                entries[0]["pacer_doc_id"] = get_pacer_doc_id_from_doc1_url(
                    document_url
                )
                entries[0]["pacer_case_id"] = get_pacer_case_id_from_doc1_url(
                    document_url
                )
                entries[0]["pacer_seq_no"] = get_pacer_seq_no_from_doc1_url(
                    document_url
                )
                entries[0][
                    "pacer_magic_num"
                ] = get_pacer_magic_num_from_doc1_url(document_url)
            return entries
        return []

    def _get_emaiL_recipients_without_links(self, recipient_lines):
        """Gets all the email recipients of the notification

        :returns: List of email recipients with names and email addresses
        """
        email_recipients = []
        for line in recipient_lines:
            if "@" in line:
                comma_separated = list(map(clean_string, line.split(",")))
                # The first element of comma_separated looks like "Stephen Breyer sbreyerguy52@hotmail.com"
                name_and_first_email = comma_separated[0].split(" ")
                # This re-joins so the name is by itself "Stephen Breyer"
                name = " ".join(name_and_first_email[:-1])
                # This is the leftover email in that first example "sbreyerguy52@hotmail.com"
                first_email = name_and_first_email[-1]
                # The remaining emails are the tail of the comma_separated list ["sbreyer@supremecourt.gov", "sbreyer@supremestreetwear.com"]
                other_emails = comma_separated[1:]
                email_recipients.append(
                    {
                        "name": name,
                        "email_addresses": [first_email] + other_emails,
                    }
                )
        return email_recipients

    def _get_email_recipients_with_links(self, text_content):
        """Gets all the email recipients of the notification if their emails are in links

        :returns: List of email recipients with names and email addresses
        """
        # Matching names in this format is a bit less reliable. May be worth coming back to.
        end_point = self._get_docket_number()

        replacements = [
            (r"\n", ""),
            (
                r"\s{2,}|\t",
                " ",
            ),
            (
                r"\s,",
                "",
            ),
            (
                r"^.*mailed\sto:",
                "",
            ),
            (
                f"{re.escape(end_point)}.*$",
                "",
            ),
        ]

        for replacement in replacements:
            text_content = re.sub(replacement[0], replacement[1], text_content)

        recipient_parts = text_content.strip().split(" ")
        email_recipients = []
        for recipient_part in recipient_parts:
            if not len(email_recipients):
                email_recipients.append({"name": recipient_part})
            else:
                last_recipient = email_recipients[-1]
                if "@" in recipient_part:
                    if not last_recipient.get("email_addresses"):
                        last_recipient["email_addresses"] = []
                    last_recipient["email_addresses"].append(
                        re.sub(r",", "", recipient_part)
                    )
                elif last_recipient.get("email_addresses") and len(
                    last_recipient["email_addresses"]
                ):
                    email_recipients.append({"name": recipient_part})
                else:
                    last_recipient["name"] += f" {recipient_part}"
        return list(
            filter(
                lambda recipient: recipient.get("email_addresses", False)
                and len(recipient.get("email_addresses")) > 0,
                email_recipients,
            )
        )

    def _get_email_recipients(self) -> List[Dict[str, Union[str, List[str]]]]:
        """Gets all the email recipients whether they come from plain text or more HTML formatting

        :returns: List of email recipients with names and email addresses
        """
        path = '//b[contains(., "Notice has been electronically mailed to")]/following-sibling::'
        recipient_lines = self.tree.xpath(f"{path}text()")
        link_lines = self.tree.xpath(f"{path}a")
        if len(link_lines):
            return self._get_email_recipients_with_links(
                self.tree.xpath(
                    'string(//b[contains(., "Notice has been electronically mailed to")]/parent::node())'
                )
            )
        return self._get_email_recipients_with_links(" ".join(recipient_lines))


class S3NotificationEmail(NotificationEmail):
    """A subclass of the NotificationEmail report. This handles all the S3 specific format issues that come from
    SES emails automatically archived in S3.
    """

    def _combine_lines_with_proper_spaces(self, text):
        """Re-composes S3 line breaks to have proper spacing depending on line ending character

        :returns: String with spacing as read normally
        """
        lines = text.split("\n")
        combined = ""
        last_line_match = False
        for line in lines:
            match = re.search(r"=$", line)
            if match:
                combined += re.sub(r"=$", "", line)
                last_line_match = True
            elif last_line_match:
                combined += line
                last_line_match = False
            else:
                combined += f" {line}"
        return combined

    def _slice_points(self, text):
        """Provides the critical character indexes where HTML starts and ends in the S3 record.

        :returns: List with the two slice points
        """
        html_content_type_index = text.index("Content-Type: text/html")
        try:
            opening_tag_index = text.index("<html", html_content_type_index)
            closing_tag_index = text.index("</html>")
            return (
                opening_tag_index,
                closing_tag_index + 7,
            )
        except ValueError as e:
            opening_tag_index = text.index("<div", html_content_type_index)
            closing_tag_index = text.rfind("</div>")
            return (
                opening_tag_index,
                closing_tag_index + 6,
            )

    def _html_from_s3_email(self, text):
        """Pulls the HTML content, parsed with line breaks normalized for from the S3 email file

        :returns: String with proper replacements for normal HTML parsing
        """
        # Remove line ends form S3 content
        cleaned_s3_line_ends = self._combine_lines_with_proper_spaces(text)

        # Find <html /> section in S3 file.
        slice_points = self._slice_points(cleaned_s3_line_ends)
        html_only = cleaned_s3_line_ends[
            slice(slice_points[0], slice_points[1])
        ]

        # Clean special characters from S3.
        replacements = [
            (
                r"=2E",
                ".",
            ),
            (
                r"=C2=A0",
                " ",
            ),
            (
                r"=20",
                " ",
            ),
            (
                r"=3D",
                "=",
            ),
        ]
        for replacement in replacements:
            html_only = re.sub(replacement[0], replacement[1], html_only)
        return html_only

    def _parse_text(self, text):
        html_only = self._html_from_s3_email(text)
        return super()._parse_text(html_only)
