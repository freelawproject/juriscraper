from __future__ import print_function

import pprint
import re
import sys

from lxml import html

from juriscraper.lib.html_utils import strip_bad_html_tags_insecure
from juriscraper.lib.string_utils import force_unicode
from .reports import BaseReport
from ..lib.log_tools import make_default_logger

logger = make_default_logger()


class AppellateAttachmentPage(BaseReport):
    """An object for querying and parsing the appellate att. page report."""

    PATH = "doc1/"

    def __init__(self, court_id, pacer_session=None):
        super(AppellateAttachmentPage, self).__init__(court_id, pacer_session)
        # Note that parsing appellate attachment pages does not reveal the
        # document number, only the attachment numbers.

    def query(self, document_number):
        """Query the "attachment page" endpoint and set the results to self.response.

        :param document_number: The internal PACER document ID for the item.
        :return: a request response object
        """
        assert (
            self.session is not None
        ), "session attribute of DocketReport cannot be None."
        # coerce the fourth digit of the document number to 1 to ensure we get
        # the attachment page.
        document_number = document_number[:3] + "0" + document_number[4:]
        url = self.url + document_number
        logger.info(u"Querying the attachment page endpoint at URL: %s", url)
        self.response = self.session.get(url)
        self.parse()

    def _strip_bad_html_tags_insecure(self, tree):
        """Remove bad tags from HTML while leaving scripts.

        :param tree: A tree you wish to cleanup
        :type tree: lxml.html.HtmlElement

        :return: None, instead sets self.tree to a cleaned lxml.html.HtmlElement.
        """
        self.tree = strip_bad_html_tags_insecure(tree, remove_scripts=False)

    @property
    def data(self):
        """Get data back from the query for the matching document entry.

        Appellate attachments is different than the district court.  We have
        no document_id. Instead we can use the pacer_seq_no or the dls_id
        to discern which attachment goes with which docket entry.

        Additionally, the main document is not identifiable in attachments.
        It is presumed to be the document with the lowest pacer_doc_id.

        :return: If lookup fails, an empty dict. Else, a dict containing the
        following fields:
            - dls_id: The id used to generate the request from the docket.
            - case_id: The pacer case id for this case.
            - pacer_seq_no - The value of the docket row we came from.

            - attachments: A list of attached items with the following fields:
                - attachment_number: The attachment number.
                - description: A description of the item.
                - page_count: The number of pages for the attachment.
                - pacer_doc_id: The pacer doc id for the attachment (a str).

        See the JSON objects in the tests for more examples.
        """
        if self.is_valid is False:
            return {}

        rows = self.tree.xpath("//tbody/tr/td/a/parent::td/parent::tr")
        html_str = html.tostring(self.tree)
        if not rows:
            logger.info("No documents found on attachment page.")
            return {}

        result = {
            "dls_id": self._get_dls_id(),
            "case_id": self._get_pacer_case_id(html_str),
            "pacer_seq_no": self._get_pacer_seq_no(html_str),
            "attachments": [],
        }

        for row in rows:
            result["attachments"].append(
                {
                    "attachment_number": self._get_attachment_number(row),
                    "description": self._get_description_from_tr(row),
                    "page_count": self._get_page_count_from_tr(row),
                    "pacer_doc_id": self._get_pacer_doc_id(row),
                }
            )
        return result

    def _get_dls_id(self):
        """Extract the dls_id.

        The dls_id is associated with the docket row - and is one number
        off from the main document ID.  This should be used to identify
        document number row.

        In appellate attachment page, this is easy to extract with an XPath.
        :return: dls_id
        """
        try:
            rows = self.tree.xpath("//tbody/tr/td/a/@href")
            pre_doc = sorted([row.split("/")[-1] for row in rows])[0]
            return pre_doc[:3] + "0" + pre_doc[4:]
        except IndexError:
            return None

    def _get_attachment_number(self, row):
        """"Return the attachment number for an item.

        :param row: Table row as an lxml element
        :type: lxml HTML element
        :return: Attachment number for row
        :type: int
        """
        number = int(row.xpath(".//td/text()")[0].strip())
        return number

    def _get_description_from_tr(self, row):
        """Get the description from the row

        :param row: Table row
        :type: lxml HTML element
        :return: Row description
        :type: unicode
        """
        description_text_nodes = row.xpath(".//td")
        if not description_text_nodes:
            return u""
        return force_unicode(description_text_nodes[2].text_content().strip())

    @staticmethod
    def _get_page_count_from_tr(row):
        """Take a row from the attachment table and return the page count as an
        int extracted from the cell specified by index.
        """
        description_text_nodes = row.xpath(".//td")
        if not description_text_nodes:
            return None
        return int(description_text_nodes[3].text_content().strip())

    @staticmethod
    def _get_pacer_doc_id(row):
        """Take in a row from the attachment table and return the pacer_doc_id
        for the item in that row. Return None if the ID cannot be found.
        """
        try:
            row.xpath(u".//a")[0]
        except IndexError:
            # Item exists, but cannot download document. Perhaps it's sealed
            # or otherwise unavailable in PACER. This is carried over from the
            # docket report and may not be needed here, but it's a good
            # precaution.
            return None
        else:
            return row.xpath(".//td/a/@href")[0].split("/")[-1]

    @staticmethod
    def _get_pacer_case_id(html_string):
        """Get the pacer_case_id value by inspecting the original HTML

        :returns str: The pacer_case_id value
        """
        m = re.search(r"[?&]caseid=(\d+)", html_string, flags=re.I)
        if m:
            return m.group(1)

    @staticmethod
    def _get_pacer_seq_no(html_string):
        """Get pacer sequence number.

        This value corresponds to the value in the docket TR
        """
        m = re.search(r"[?&]d=(\d+)&outputForm", html_string, flags=re.I)
        if m:
            return m.group(1)


def _main():
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.pacer.attachment_page filepath")
        print("Please provide a path to an HTML file to parse.")
        sys.exit(1)
    report = AppellateAttachmentPage(
        "cand"
    )  # Court ID is only needed for querying.
    filepath = sys.argv[1]
    print("Parsing HTML file at {}".format(filepath))
    with open(filepath, "r") as f:
        text = f.read().decode("utf-8")
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
