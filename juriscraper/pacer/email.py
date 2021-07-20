import re
from datetime import date
from typing import Dict, List, Optional, Union

from ..lib.string_utils import clean_string, convert_date_string, harmonize
from .docket_report import BaseDocketReport
from .reports import BaseReport
from .utils import (get_pacer_doc_id_from_doc1_url,
                    get_pacer_seq_no_from_doc1_anchor)


class NotificationEmail(BaseDocketReport, BaseReport):
    def __init__(self, court_id):
        self.court_id = court_id
        super(NotificationEmail, self).__init__(court_id)

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

    def _get_case_name(self) -> str:
        path = '//td[contains(., "Case Name:")]/following-sibling::td[1]'
        case_name = self._xpath_text_0(self.tree, path)
        if not case_name:
            case_name = "Unknown Case Title"
        return clean_string(harmonize(case_name))

    def _get_docket_number(self) -> str:
        path = '//td[contains(., "Case Number:")]/following-sibling::td[1]/a/text()'
        return self._parse_docket_number_strs(self.tree.xpath(path))

    def _get_date_filed(self) -> date:
        date_filed = re.search(
            "filed\son\s([\d|\/]*)",
            clean_string(self.tree.text_content()),
            flags=re.IGNORECASE,
        )
        return convert_date_string(
            date_filed[0].lower().replace("filed on ", "")
        )

    def _get_document_number(self) -> str:
        path = '//td[contains(., "Document Number:")]/following-sibling::td[1]'
        text = self.tree.xpath(path)[0].text_content()
        words = re.split(r"\(|\s", clean_string(text))
        return words[0]

    def _get_doc1_anchor(self) -> str:
        try:
            path = '//td[contains(., "Document Number:")]/following-sibling::td[1]/a'
            return self.tree.xpath(path)[0]
        except IndexError:
            return None

    def _get_docket_entries(
        self,
    ) -> List[Dict[str, Optional[Union[str, date]]]]:
        try:
            path = '//strong[contains(., "Docket Text:")]/following-sibling::font[1]/b/text()'
            description = clean_string(self.tree.xpath(path)[0])
            entries = [
                {
                    "date_filed": self._get_date_filed(),
                    "description": description,
                    "document_number": self._get_document_number(),
                    "pacer_doc_id": None,
                    "pacer_seq_no": None,
                }
            ]
            anchor = self._get_doc1_anchor()
            if anchor is not None:
                entries[0]["pacer_doc_id"] = get_pacer_doc_id_from_doc1_url(
                    anchor.xpath("./@href")[0]
                )
                entries[0]["pacer_seq_no"] = get_pacer_seq_no_from_doc1_anchor(
                    anchor
                )
            return entries
        except IndexError:
            return []

    def _get_email_recipients(self) -> List[Dict[str, Union[str, List[str]]]]:
        path = '//b[contains(., "Notice has been electronically mailed to")]/following-sibling::text()'
        recipient_lines = self.tree.xpath(path)
        email_recipients = []
        for line in recipient_lines:
            if "@" in line:
                comma_separated = list(map(clean_string, line.split(",")))
                # The first element of comma_separatd looks like "Stephen Breyer sbreyerguy52@hotmail.com"
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


class S3NotificationEmail(NotificationEmail):
    def _combine_lines_with_proper_spaces(self, text):
        lines = text.split("\n")
        combined = ""
        last_line_match = False
        for line in lines:
            stripped = line.strip()
            match = re.search(r"=$", stripped)
            if match:
                combined += re.sub(r"=$", "", stripped)
                last_line_match = True
            elif last_line_match:
                combined += stripped
                last_line_match = False
            else:
                combined += " " + stripped
        return combined

    def _slice_points(self, text):
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
        # Remove line ends form S3 content
        cleaned_s3_line_ends = self._combine_lines_with_proper_spaces(text)

        # Find <html /> section in S3 file.
        slice_points = self._slice_points(cleaned_s3_line_ends)
        html_only = cleaned_s3_line_ends[
            slice(slice_points[0], slice_points[1])
        ]

        # Clean special characters from S3.
        return re.sub(r"=3D", "=", html_only)

    def _parse_text(self, text):
        html_only = self._html_from_s3_email(text)
        return super()._parse_text(html_only)
