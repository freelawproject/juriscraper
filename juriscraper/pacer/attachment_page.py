from .reports import BaseReport
from ..lib.log_tools import make_default_logger
from ..lib.string_utils import force_unicode

logger = make_default_logger()


class AttachmentPage(BaseReport):
    """An object for querying and parsing the attachment page report. """

    PATH = 'doc1/'

    def query(self, document_number):
        """Query the "attachment page" endpoint and set the results to self.response.

        :param document_number: The internal PACER document ID for the item.
        :return: a request response object
        """
        assert self.session is not None, \
            "session attribute of DocketReport cannot be None."
        url = self.url + document_number
        logger.info(u'Querying the attachment page endpoint at URL: %s' % url)
        self.response = self.session.get(url)
        self.parse()

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
        rows = self.tree.xpath('//tr[.//a]')
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
