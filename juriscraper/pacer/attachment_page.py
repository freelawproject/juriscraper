from lxml import etree

from ..lib.html_utils import (
    set_response_encoding, clean_html, fix_links_in_lxml_tree,
    get_html5_parsed_text
)
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import force_unicode

logger = make_default_logger()


class AttachmentPage(object):
    """An object for querying and parsing the attachment page report. """
    def __init__(self, court_id, pacer_session=None):
        self.court_id = court_id
        self.session = pacer_session
        self.html_tree = None
        super(AttachmentPage, self).__init__()

    @property
    def url(self):
        if self.court_id == 'psc':
            return "https://dcecf.psc.uscourts.gov/doc1/"
        else:
            return "https://ecf.%s.uscourts.gov/doc1/" % self.court_id

    def query(self, document_number):
        """Query the "attachment page" endpoint and return results.

        :param document_number: The internal PACER document ID for the item.
        :return: a request response object
        """
        assert self.session is not None, \
            "session attribute of DocketReport cannot be None."
        url = self.url + document_number
        logger.info(u'Querying the attachment page endpoint at URL: %s' % url)
        return self.session.get(url, timeout=300)

    def parse_text(self, text):
        """Parse the HTML as unicode text and set self.html_tree

        :param text: A unicode object
        :return: None
        """
        assert isinstance(text, unicode), \
            "Input must be unicode, not %s" % type(text)
        text = clean_html(text)
        tree = get_html5_parsed_text(text)
        etree.strip_elements(tree, u'script')
        tree.rewrite_links(fix_links_in_lxml_tree, base_href=self.url)
        self.html_tree = tree

    def parse_response(self, response):
        """Parse HTML provided in a requests.response object and set
        self.html_tree

        :param response: a python request response object
        :return: None
        """
        response.raise_for_status()
        set_response_encoding(response)
        self.parse_text(response.text)

    @property
    def data(self):
        """Get data back from the query for the matching document entry.

        :return: A dict containing the following fields:
            - document_number: The document number we're working with.
            - page_count: The number of pages of the item
            - attachments: A list of attached items with the following fields:
                - attachment_number: The attachment number.
                - description: A description of the item.
                - page_count: The number of pages.

        See the JSON objects in the tests for more examples.
        """
        rows = self.html_tree.xpath('//tr[.//a]')
        if not rows:
            logger.info("No documents found on attachment page.")
            return {}

        first_row = rows.pop(0)
        result = {
            'document_number': int(first_row.xpath('.//a/text()')[0].strip()),
            'page_count': self._get_page_count_from_tr(first_row, 2),
            'attachments': []
        }
        for row in rows:
            result['attachments'].append({
                'attachment_number': int(row.xpath('.//a/text()')[0].strip()),
                'description': force_unicode(
                    row.xpath('./td[2]//text()')[0].strip()
                ),
                'page_count': self._get_page_count_from_tr(row, 3),
            })

        return result

    @staticmethod
    def _get_page_count_from_tr(tr, index):
        """Take a row from the attachment table and return the page count as an
        int extracted from the cell specified by index.
        """
        pg_cnt_str = tr.xpath('./td[%s]/text()' % index)[0].strip()
        return int(pg_cnt_str.split()[0])
