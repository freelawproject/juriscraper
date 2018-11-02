import pprint
import re
import sys

from .reports import BaseReport
from .utils import get_pacer_doc_id_from_doc1_url, reverse_goDLS_function
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import force_unicode

logger = make_default_logger()


class AttachmentPage(BaseReport):
    """An object for querying and parsing the attachment page report. """

    PATH = 'doc1/'

    def __init__(self, court_id, pacer_session=None):
        super(AttachmentPage, self).__init__(court_id, pacer_session)
        # Note that parsing bankruptcy attachment pages does not reveal the
        # document number, only the attachment numbers.
        self.is_bankruptcy = self.court_id.endswith('b')

    def query(self, document_number):
        """Query the "attachment page" endpoint and set the results to self.response.

        :param document_number: The internal PACER document ID for the item.
        :return: a request response object
        """
        assert self.session is not None, \
            "session attribute of DocketReport cannot be None."
        # coerce the fourth digit of the document number to 1 to ensure we get
        # the attachment page.
        document_number = document_number[:3] + "0" + document_number[4:]
        url = self.url + document_number
        logger.info(u'Querying the attachment page endpoint at URL: %s', url)
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

        rows = self.tree.xpath('//tr[.//a]')
        if not rows:
            logger.info("No documents found on attachment page.")
            return {}

        first_row = rows.pop(0)
        result = {
            'document_number': self._get_document_number(),
            'page_count': self._get_page_count_from_tr(first_row),
            'file_size_str': self._get_file_size_str_from_tr(first_row),
            'pacer_doc_id': self._get_pacer_doc_id(first_row),
            'pacer_case_id': self._get_pacer_case_id(),
            'pacer_seq_no': self._get_pacer_seq_no_from_tr(first_row),
            'attachments': []
        }
        if result['document_number'] is None and not self.is_bankruptcy:
            # Abort. Sometimes some attachment pages we receive have a blank
            # area instead of having a proper document number. When going to
            # PACER to reproduce this, things look fine, so I don't know why we
            # get the bad data. In any case, simply give up since we can't do
            # much without a document number.
            return {}
        for row in rows:
            result['attachments'].append({
                'attachment_number': self._get_attachment_number(row),
                'description': self._get_description_from_tr(row),
                'page_count': self._get_page_count_from_tr(row),
                'file_size_str': self._get_file_size_str_from_tr(row),
                'pacer_doc_id': self._get_pacer_doc_id(row),
                # It may not be needed to reparse the seq_no
                # for each row, but we may as well. So far, it
                # has always been the same as the main document.
                'pacer_seq_no': self._get_pacer_seq_no_from_tr(row),
            })

        return result

    def _get_document_number(self):
        """Return the document number for an item.

        In district court attachment pages, this is easy to extract with an
        XPath. In bankruptcy cases, it's simply not there.
        """
        if self.is_bankruptcy:
            return None
        else:
            try:
                path = '//tr[contains(., "Document Number")]//a/text()'
                return int(self.tree.xpath(path)[0].strip())
            except IndexError:
                return None

    def _get_attachment_number(self, row):
        """Return the attachment number for an item.

        In district courts, this can be easily extracted. In bankruptcy courts,
        you must extract it, then subtract 1 from the value since these are
        tallied and include the main document.
        """
        number = int(row.xpath('.//a/text()')[0].strip())
        if self.is_bankruptcy:
            return number - 1
        else:
            return number

    def _get_description_from_tr(self, row):
        """Get the description from the row"""
        if not self.is_bankruptcy:
            index = 2
        else:
            index = 3
        description_text_nodes = row.xpath('./td[%s]//text()' % index)
        if not description_text_nodes:
            # No text in the cell.
            return u''
        else:
            description = description_text_nodes[0].strip()
            return force_unicode(description)

    @staticmethod
    def _get_page_count_from_tr(tr):
        """Take a row from the attachment table and return the page count as an
        int extracted from the cell specified by index.
        """
        pg_cnt_str_nodes = tr.xpath('./td[contains(., "page")]/text()')
        if not pg_cnt_str_nodes:
            # It's a restricted document without page count information.
            return None
        else:
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
    def _get_file_size_str_from_tr(tr):
        """Take a row from the attachment table and return the number of bytes
        as an int.
        """
        cells = tr.xpath('./td')
        last_cell_contents = cells[-1].text_content()
        units = ['kb', 'mb']
        if any(unit in last_cell_contents.lower() for unit in units):
            return last_cell_contents
        return ""

    @staticmethod
    def _get_pacer_doc_id(row):
        """Take in a row from the attachment table and return the pacer_doc_id
        for the item in that row. Return None if the ID cannot be found.
        """
        try:
            url = row.xpath(u'.//a')[0]
        except IndexError:
            # Item exists, but cannot download document. Perhaps it's sealed
            # or otherwise unavailable in PACER. This is carried over from the
            # docket report and may not be needed here, but it's a good
            # precaution.
            return None
        else:
            doc1_url = url.xpath('./@href')[0]
            return get_pacer_doc_id_from_doc1_url(doc1_url)

    @staticmethod
    def _get_pacer_seq_no_from_tr(row):
        """Take a row of the attachment page, and return the sequence number
        from the goDLS function.
        """
        try:
            url = row.xpath(u'.//a')[0]
        except IndexError:
            # No link in the row. Maybe its sealed.
            pass
        else:
            try:
                onclick = url.xpath('./@onclick')[0]
            except IndexError:
                # No onclick on this row.
                pass
            else:
                if 'goDLS' in onclick:
                    go_dls_parts = reverse_goDLS_function(onclick)
                    return go_dls_parts['de_seq_num']

        # 1. Couldn't find a link in the row: Maybe it's sealed.
        # 2. No onclick on the row.
        # 3. No goDLS in the onclick
        return None

    def _get_pacer_case_id(self):
        """Get the pacer_case_id value by inspecting the HTML

        :returns str: The pacer_case_id value
        """
        # Start by inspecting all the links
        urls = self.tree.xpath('//a')
        for url in urls:
            try:
                onclick = url.xpath('./@onclick')[0]
            except IndexError:
                continue
            else:
                if 'goDLS' not in onclick:
                    # Some other onclick we don't care about.
                    continue
                go_dls_parts = reverse_goDLS_function(onclick)
                return go_dls_parts['caseid']

        # If that fails, try inspecting the input elements
        input_els = self.tree.xpath('//input')
        for input_el in input_els:
            try:
                onclick = input_el.xpath('./@onclick')[0]
            except IndexError:
                continue
            else:
                m = re.search(r'[?&]caseid=(\d+)', onclick, flags=re.I)
                if m:
                    return m.group(1)


def _main():
    if len(sys.argv) != 2:
        print "Usage: python -m juriscraper.pacer.attachment_page filepath"
        print "Please provide a path to an HTML file to parse."
        sys.exit(1)
    report = AttachmentPage('cand')  # Court ID is only needed for querying.
    filepath = sys.argv[1]
    print "Parsing HTML file at %s" % filepath
    with open(filepath, 'r') as f:
        text = f.read().decode('utf-8')
    report._parse_text(text)
    pprint.pprint(report.data, indent=2)


if __name__ == "__main__":
    _main()
