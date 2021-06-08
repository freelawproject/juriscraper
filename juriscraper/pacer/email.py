import datetime
import re

from ..lib.string_utils import (
    clean_string,
    convert_date_string,
    harmonize,
    numbers_only,
)
from .reports import BaseReport


class NotificationEmail(BaseReport):
    def __init__(self, court_id):
        self.court_id = court_id

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

    def _get_case_name(self):
        try:
            path = '//td[contains(., "Case Name:")]/following-sibling::td[1]/text()'
            case_name = harmonize(self.tree.xpath(path)[0])
        except IndexError:
            case_name = "Unknown Case Title"
        return case_name

    def _get_docket_number(self):
        path = '//td[contains(., "Case Number:")]/following-sibling::td[1]/a/text()'
        return clean_string(self.tree.xpath(path)[0])

    def _get_date_filed(self):
        date_filed = re.search(
            "filed\son\s([\d|\/]*)",
            self.tree.text_content(),
            flags=re.IGNORECASE,
        )
        return convert_date_string(
            date_filed[0].lower().replace("filed on ", "")
        )

    def _get_document_number(self):
        document_number = self._get_document_number_from_link()
        if document_number is not None:
            return document_number
        return self._get_document_number_from_text()

    def _get_document_number_from_link(self):
        try:
            path = '//td[contains(., "Document Number:")]/following-sibling::td[1]/a/text()'
            return numbers_only(self.tree.xpath(path)[0])[0]
        except IndexError:
            return None

    def _get_document_number_from_text(self):
        try:
            path = '//td[contains(., "Document Number:")]/following-sibling::td[1]/text()'
            return numbers_only(self.tree.xpath(path)[0])[0]
        except IndexError:
            return None

    def _get_document_url(self):
        try:
            path = '//td[contains(., "Document Number:")]/following-sibling::td[1]/a/@href'
            return self.tree.xpath(path)[0]
        except IndexError:
            return None

    def _get_docket_entries(self):
        try:
            path = '//strong[contains(., "Docket Text:")]/following-sibling::font[1]/b/text()'
            description = clean_string(self.tree.xpath(path)[0])
            return [
                {
                    "date_filed": self._get_date_filed(),
                    "description": description,
                    "document_number": self._get_document_number(),
                    "document_url": self._get_document_url(),
                    "pacer_doc_id": None,
                    "pacer_seq_no": None,
                }
            ]
        except IndexError:
            return []

    def _get_email_recipients(self):
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
