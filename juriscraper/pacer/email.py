import datetime
import re

from ..lib.string_utils import clean_string, convert_date_string, harmonize
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
