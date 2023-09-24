import pprint
import re
import sys

from ..lib.log_tools import make_default_logger
from ..lib.string_utils import force_unicode
from .reports import BaseReport
from .utils import (
    get_court_id_from_doc_id_prefix,
    get_pacer_doc_id_from_doc1_url,
    reverse_goDLS_function,
)

logger = make_default_logger()


class AttachmentPage(BaseReport):
    """An object for querying and parsing the attachment page report."""

    PATH = "doc1/"

    def __init__(self, court_id, pacer_session=None):
        super().__init__(court_id, pacer_session)
        # Note that parsing bankruptcy attachment pages does not reveal the
        # document number, only the attachment numbers.
        self.is_bankruptcy = self.court_id.endswith("b")

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
        document_number = f"{document_number[:3]}0{document_number[4:]}"
        url = self.url + document_number
        logger.info("Querying the attachment page endpoint at URL: %s", url)
        self.response = self.session.get(url)
        self.parse()

    @property
    def data(self):
        """Get data back from the query for the matching document entry.

        :return: If lookup fails, an empty dict. Else, a dict containing the
        following fields:
            - document_number: The document number we're working with.
            - page_count: The number of pages of the item
            - file_size_str: The size of the file as a str or null if unknown
            - pacer_doc_id: The doc ID for the main document.
            - attachments: A list of attached items with the following fields:
                - attachment_number: The attachment number.
                - description: A description of the item.
                - page_count: The number of pages.
                - file_size_str: The size of the file as a str or null if
                  unknown
                - pacer_doc_id: The document ID for the attachment (a str).

        See the JSON objects in the tests for more examples.
        """
        if self.is_valid is False:
            return {}

        rows = self.tree.xpath("//tr[.//a]")
        if not rows:
            logger.info("No documents found on attachment page.")
            return {}

        first_num = self._get_name_attachment_number(rows[0])
        # First row is an attachment
        if first_num is not None and first_num != 0:
            first_row = rows[0]
            first_row_attachment = True
        else:
            first_row = rows.pop(0)
            first_row_attachment = False
        result = {
            "document_number": self._get_document_number(),
            "pacer_doc_id": self._get_pacer_doc_id(first_row),
            "pacer_case_id": self._get_pacer_case_id(),
            "pacer_seq_no": self._get_pacer_seq_no_from_tr(first_row),
            "attachments": [],
        }
        if first_row_attachment:
            result["page_count"] = None
            result["file_size_str"] = ""
        else:
            result["page_count"] = self._get_page_count_from_tr(first_row)
            file_size_bytes = self._get_file_size_bytes_from_tr(first_row)
            if file_size_bytes is not None:
                result["file_size_bytes"] = file_size_bytes
            result["file_size_str"] = self._get_file_size_str_from_tr(
                first_row
            )
        for row in rows:
            attachment = {
                "attachment_number": self._get_attachment_number(row),
                "description": self._get_description_from_tr(row),
                "page_count": self._get_page_count_from_tr(row),
                "file_size_str": self._get_file_size_str_from_tr(row),
                "pacer_doc_id": self._get_pacer_doc_id(row),
                # It may not be needed to reparse the seq_no
                # for each row, but we may as well. So far, it
                # has always been the same as the main document.
                "pacer_seq_no": self._get_pacer_seq_no_from_tr(row),
            }
            file_size_bytes = self._get_file_size_bytes_from_tr(row)
            if file_size_bytes is not None:
                attachment["file_size_bytes"] = file_size_bytes
            result["attachments"].append(attachment)

        return result

    def _get_document_number(self):
        """Return the document number for an item.

        In district court attachment pages, this is easy to extract with an
        XPath. In bankruptcy cases, it's simply not there.
        """
        if self.is_bankruptcy:
            return None

        # First try inspecting the input elements
        input_els = self.tree.xpath("//input")
        for input_el in input_els:
            try:
                name = input_el.xpath("./@name")[0]
            except IndexError:
                continue
            else:
                split = name.split("_")
                # Document 16 name field example "document_16_0"
                if len(split) == 3 and split[0] == "document":
                    document_string = split[1]
                    # Any other matches will be invalid if this is empty
                    if document_string == "":
                        return None
                    document_number = int(document_string)
                    # Ensure document number is valid
                    if document_number != 0:
                        return document_number

        # There are two styles of attachment menus. Try them both.
        paths = (
            '//tr[contains(., "Document Number")]//a/text()',
            '//tr[contains(., "Main Document")]//a/text()',
        )
        for path in paths:
            try:
                return int(self.tree.xpath(path)[0].strip())
            except IndexError:
                continue
        return None

    def _decrement_attachment_index(self, row):
        """Return if we need to decrement the attachment index.

        We need to do this for all bankruptcy courts and old attachment pages
        in some district courts.

        For district courts we need to use a mapping table with the last dlsid
        that requires a decrement.

        Note that the decrement check must be done for each row in case any
        attachments in the page have sequences after the changeover as any
        updated attachments with a dlsid after the changeover should not be
        decremented.
        """
        sub_dlsid = {
            "akd": 682797,
            "ared": 1906030,
            "cacd": 9630188,
            "ctd": 2414673,
            "flmd": 7734601,
            "flnd": 2613796,
            "gamd": 995021,
            "gasd": 1159201,
            "hid": 1078891,
            "ilnd": 8278610,
            "iand": 899130,
            "innd": 1560410,
            "iasd": 1192972,
            "kyed": 2087957,
            "kywd": 1738484,
            "mad": 3618527,
            "mied": 4148337,
            "miwd": 2358030,
            "moed": 3299716,
            "msnd": 888190,
            "mssd": 2476698,
            "nced": 1868202,
            "ncmd": 1093535,
            "ndd": 299419,
            "ned": 1868173,
            "nvd": 3153010,
            "nyed": 6778644,
            "nynd": 1829022,
            "nysd": 8012889,
            "nywd": 1862410,
            "oked": 388419,
            "ord": 3322370,
            "pamd": 3122200,
            "sdd": 1239147,
            "txed": 3830781,
            "txnd": 4975453,
            "utd": 1745928,
            "vaed": 1338618,
            "waed": 1349144,
            "wawd": 3755107,
            "wied": 1420356,
            "wyd": 797428,
        }
        if self.is_bankruptcy:
            return True
        doc_id = self._get_pacer_doc_id(row)
        court_id = get_court_id_from_doc_id_prefix(doc_id[:3])
        if court_id not in sub_dlsid:
            return False
        dlsid = int(doc_id[3:])
        if sub_dlsid[court_id] < dlsid:
            return False
        return True

    def _get_name_attachment_number(self, row):
        try:
            name = row.xpath(".//input/@name")[0]
        except IndexError:
            return None
        else:
            split = name.split("_")
            # Document 16 name field example "document_16_0"
            if len(split) == 3 and split[0] == "document":
                return int(split[2])
        return None

    def _get_attachment_number(self, row):
        """Return the attachment number for an item.

        In district courts, this can be easily extracted. In bankruptcy courts,
        you must extract it, then subtract 1 from the value since these are
        tallied and include the main document.
        """
        number = self._get_name_attachment_number(row)
        if number is None:
            number = int(row.xpath(".//a/text()")[0].strip())
        if self._decrement_attachment_index(row):
            return number - 1
        return number

    def _get_description_from_tr(self, row):
        """Get the description from the row"""
        if not self.is_bankruptcy:
            index = 2
            # Some NEFs attachment pages for some courts have an extra column
            # (see nyed_123019137279), use index 3 to get the description
            columns_in_row = row.xpath(f"./td")
            if len(columns_in_row) == 5:
                index = 3
        else:
            index = 3

        description_text_nodes = row.xpath(f"./td[{index}]//text()")
        if not description_text_nodes:
            # No text in the cell.
            return ""
        description = description_text_nodes[0].strip()
        return force_unicode(description)

    @staticmethod
    def _get_input_value_from_tr(tr, idx):
        """Take a row from the attachment table and return the input value by
        index.
        """
        try:
            input = tr.xpath(".//input")[0]
        except IndexError:
            return None
        else:
            # initial value string "23515655-90555-2"
            # "90555" is size in bytes "2" is pages
            value = input.xpath("./@value")[0]
            split_value = value.split("-")
            if len(split_value) != 3:
                return None
            return split_value[idx]

    @staticmethod
    def _get_page_count_from_tr_input_value(tr):
        """Take a row from the attachment table and return the page count as an
        int extracted from the input value.
        """
        count = AttachmentPage._get_input_value_from_tr(tr, 2)
        if count is not None:
            return int(count)

    @staticmethod
    def _get_page_count_from_tr(tr):
        """Take a row from the attachment table and return the page count as an
        int extracted from the cell specified by index.
        """
        pg_cnt_input = AttachmentPage._get_page_count_from_tr_input_value(tr)
        if pg_cnt_input:
            return pg_cnt_input
        pg_cnt_str_nodes = tr.xpath('./td[contains(., "page")]/text()')
        if not pg_cnt_str_nodes:
            # It's a restricted document without page count information.
            return None

        for pg_cnt_str_node in pg_cnt_str_nodes:
            try:
                pg_cnt_str = pg_cnt_str_node.strip()
                return int(pg_cnt_str.split()[0])
            except ValueError:
                # Happens when the description field contains the
                # word "page" and gets caught by the xpath. Just
                # press on.
                continue

    @staticmethod
    def _get_file_size_bytes_from_tr(tr):
        """Take a row from the attachment table and return the number of bytes
        as an int.
        """
        file_size_str = AttachmentPage._get_input_value_from_tr(tr, 1)
        if file_size_str is None:
            return None
        file_size = int(file_size_str)
        if file_size == 0:
            return None
        return file_size

    @staticmethod
    def _get_file_size_str_from_tr(tr):
        """Take a row from the attachment table and return the number of bytes
        as an int.
        """
        cells = tr.xpath("./td")
        last_cell_contents = cells[-1].text_content()
        units = ["kb", "mb"]
        if any(unit in last_cell_contents.lower() for unit in units):
            return last_cell_contents.strip()
        return ""

    @staticmethod
    def _get_pacer_doc_id(row):
        """Take in a row from the attachment table and return the pacer_doc_id
        for the item in that row. Return None if the ID cannot be found.
        """
        try:
            url = row.xpath(".//a")[0]
        except IndexError:
            # Item exists, but cannot download document. Perhaps it's sealed
            # or otherwise unavailable in PACER. This is carried over from the
            # docket report and may not be needed here, but it's a good
            # precaution.
            return None
        else:
            doc1_url = url.xpath("./@href")[0]
            return get_pacer_doc_id_from_doc1_url(doc1_url)

    @staticmethod
    def _get_pacer_seq_no_from_tr(row):
        """Take a row of the attachment page, and return the sequence number
        from the goDLS function.
        """
        try:
            url = row.xpath(".//a")[0]
        except IndexError:
            # No link in the row. Maybe its sealed.
            pass
        else:
            try:
                onclick = url.xpath("./@onclick")[0]
            except IndexError:
                # No onclick on this row.
                pass
            else:
                if "goDLS" in onclick:
                    go_dls_parts = reverse_goDLS_function(onclick)
                    return go_dls_parts["de_seq_num"]

        # 1. Couldn't find a link in the row: Maybe it's sealed.
        # 2. No onclick on the row.
        # 3. No goDLS in the onclick
        return None

    def _get_pacer_case_id(self):
        """Get the pacer_case_id value by inspecting the HTML

        :returns str: The pacer_case_id value
        """
        # Start by inspecting all the links
        urls = self.tree.xpath("//a")
        for url in urls:
            try:
                onclick = url.xpath("./@onclick")[0]
            except IndexError:
                continue
            else:
                if "goDLS" not in onclick:
                    # Some other onclick we don't care about.
                    continue
                go_dls_parts = reverse_goDLS_function(onclick)
                return go_dls_parts["caseid"]

        # If that fails, try inspecting the input elements
        input_els = self.tree.xpath("//input")
        for input_el in input_els:
            try:
                onclick = input_el.xpath("./@onclick")[0]
            except IndexError:
                continue
            else:
                m = re.search(r"[?&]caseid=(\d+)", onclick, flags=re.I)
                if m:
                    return m.group(1)


def _main():
    if len(sys.argv) != 2:
        print("Usage: python -m juriscraper.pacer.attachment_page filepath")
        print("Please provide a path to an HTML file to parse.")
        sys.exit(1)
    report = AttachmentPage("cand")  # Court ID is only needed for querying.
    filepath = sys.argv[1]
    print(f"Parsing HTML file at {filepath}")
    with open(filepath) as f:
        text = f.read().decode("utf-8")
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
