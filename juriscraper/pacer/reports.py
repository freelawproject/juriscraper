# coding=utf-8
import re
from lxml import etree
from six.moves.urllib.parse import urljoin

from .utils import make_doc1_url, is_pdf
from ..lib.html_utils import (
    set_response_encoding, clean_html, fix_links_in_lxml_tree,
    get_html5_parsed_text, get_html_parsed_text,
)
from ..lib.log_tools import make_default_logger

logger = make_default_logger()


class BaseReport(object):
    """A base report for working with pages on PACER."""

    REDIRECT_REGEX = re.compile('window\.\s*?location\s*=\s*"(.*)"\s*;')

    # Subclasses should override PATH
    PATH = ''

    def __init__(self, court_id, pacer_session=None):
        self.court_id = court_id
        self.session = pacer_session
        self.tree = None
        self.response = None
        super(BaseReport, self).__init__()

    @property
    def url(self):
        if self.court_id == 'psc':
            return "https://dcecf.psc.uscourts.gov/%s" % self.PATH
        else:
            return "https://ecf.%s.uscourts.gov/%s" % (self.court_id, self.PATH)

    def query(self, *args, **kwargs):
        """Query PACER and set self.response with the response."""
        raise NotImplementedError(".query() must be overridden")

    def parse(self):
        """Parse the data provided in a requests.response object and set
        self.tree to be an lxml etree. In most cases, you won't need to call
        this since it will be automatically called by self.query, if needed.

        :return: None
        """
        self.response.raise_for_status()
        set_response_encoding(self.response)
        self._parse_text(self.response.text)

    def _parse_text(self, text):
        """Parse the HTML as unicode text and set self.tree

        This is a particularly critical method when running tests, which pull
        from local disk instead of from a query response. This is also used
        when data comes from a source other than self.query() (such as a user
        upload). This method should probably be made public as .parse_text().

        :param text: A unicode object
        :return: None
        """
        assert isinstance(text, unicode), \
            "Input must be unicode, not %s" % type(text)
        text = clean_html(text)
        self.tree = get_html5_parsed_text(text)
        etree.strip_elements(self.tree, u'script')
        self.tree.rewrite_links(fix_links_in_lxml_tree, base_href=self.url)

    @property
    def data(self):
        """Extract the data from the tree and return it."""
        raise NotImplementedError('.data() must be overridden.')

    def download_pdf(self, pacer_case_id, pacer_document_number):
        """Download a PDF from PACER.

        Note that this doesn't support attachments yet.

        :returns: request.Response object containing a PDF, if one can be found
        (is not sealed, gone, etc.). Else, returns None.
        """
        timeout = (60, 300)
        url = make_doc1_url(self.court_id, pacer_document_number, True)
        data = {
            'case_id': pacer_case_id,
            'got_receipt': '1',
        }

        logger.info("GETting PDF at URL: %s with params: %s" % (url, data))
        r = self.session.get(url, params=data, timeout=timeout)

        if u'This document is not available' in r.text:
            logger.error("Document not available in case: %s at %s" %
                         (url, pacer_case_id))
            return None

        # Some pacer sites use window.location in their JS, so we have to look
        # for that. See: oknd, 13-cv-00357-JED-FHM, doc #24. But, be warned, you
        # can only catch the redirection with JS off.
        m = self.REDIRECT_REGEX.search(r.text)
        if m is not None:
            r = self.session.get(urljoin(url, m.group(1)))
            r.raise_for_status()

        # The request above sometimes generates an HTML page with an iframe
        # containing the PDF, and other times returns the PDF directly. ∴ either
        # get the src of the iframe and download the PDF or just return the pdf.
        r.raise_for_status()
        if is_pdf(r):
            logger.info('Got PDF binary data for case %s at: %s' % (url, data))
            return r

        text = clean_html(r.text)
        tree = get_html_parsed_text(text)
        tree.rewrite_links(fix_links_in_lxml_tree,
                           base_href=r.url)
        try:
            iframe_src = tree.xpath('//iframe/@src')[0]
        except IndexError:
            if 'pdf:Producer' in text:
                logger.error("Unable to download PDF. PDF content was placed "
                             "directly in HTML. URL: %s, caseid: %s" %
                             (url, pacer_case_id))
            else:
                logger.error("Unable to download PDF. PDF not served as binary "
                             "data and unable to find iframe src attribute. "
                             "URL: %s, caseid: %s" % (url, pacer_case_id))
            return None

        r = self.session.get(iframe_src, timeout=timeout)
        if is_pdf(r):
            logger.info('Got iframed PDF data for case %s at: %s' %
                        (url, iframe_src))

        return r
