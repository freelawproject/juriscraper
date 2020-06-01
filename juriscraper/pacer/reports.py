# coding=utf-8
import re

import six
from lxml import etree
from lxml.html import HtmlElement
from six.moves.urllib.parse import urljoin

from .utils import is_pdf, make_doc1_url
from ..lib.html_utils import (
    clean_html,
    fix_links_in_lxml_tree,
    get_html5_parsed_text,
    get_html_parsed_text,
    set_response_encoding,
)
from ..lib.log_tools import make_default_logger

logger = make_default_logger()


# Patch the HtmlElement class to add a function that can handle regular
# expressions within XPath queries. See usages throughout AppellateDocketReport.
def re_xpath(self, path):
    return self.xpath(
        path, namespaces={"re": "http://exslt.org/regular-expressions"}
    )


HtmlElement.re_xpath = re_xpath


class BaseReport(object):
    """A base report for working with pages on PACER."""

    REDIRECT_REGEX = re.compile('window\.\s*?location\s*=\s*"(.*)"\s*;')

    # Subclasses should override PATH
    PATH = ""

    # Strings below (and in subclasses) are used to identify HTML that should
    # not be parsed or processed for a variety of reasons. Spaces in the
    # strings below are converted to \s whitespace searches using regexes.
    ERROR_STRINGS = [
        "MetaMask.*web3",
        'console\.log\(".*CloudMask',
        "Drumpf",
    ]

    def __init__(self, court_id, pacer_session=None):
        self.court_id = court_id
        self.session = pacer_session
        self.tree = None
        self.response = None
        self.is_valid = None
        super(BaseReport, self).__init__()

    @property
    def url(self):
        if self.court_id == "psc":
            return "https://dcecf.psc.uscourts.gov/%s" % self.PATH
        else:
            return "https://ecf.%s.uscourts.gov/%s" % (
                self.court_id,
                self.PATH,
            )

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
        assert isinstance(
            text, six.text_type
        ), "Input must be unicode, not %s" % type(text)
        text = clean_html(text)
        self.check_validity(text)
        if self.is_valid:
            self.tree = get_html5_parsed_text(text)
            etree.strip_elements(self.tree, u"script")
            self.tree.rewrite_links(fix_links_in_lxml_tree, base_href=self.url)

    def check_validity(self, text):
        """Place sanity checks here to make sure that the returned text is
        valid and not an error page or some other kind of problem.

        Set self.is_valid flag to True or False
        """
        for error_string in self.ERROR_STRINGS:
            error_string_re = re.compile(
                "\s+".join(error_string.split()), flags=re.I
            )
            if error_string_re.search(text):
                self.is_valid = False
                return
        self.is_valid = True

    @property
    def data(self):
        """Extract the data from the tree and return it."""
        raise NotImplementedError(".data() must be overridden.")

    def _query_pdf_download(self, pacer_case_id, pacer_doc_id, got_receipt):
        """Query the doc1 download URL.

        :param pacer_case_id: The case ID for the case. Used for disambiguating
        which case the document is associated with when a pacer_doc_id is used
        in multiple cases.
        :param pacer_doc_id: The doc id for the document
        :param got_receipt: Whether to get the receipt for the page ('0') or
        get the PDF itself ('1').
        :return the Request.response object and the url queried
        """
        url = make_doc1_url(self.court_id, pacer_doc_id, True)
        data = {
            "caseid": pacer_case_id,
            "got_receipt": got_receipt,
            # Include the PDF header where possible. Different courts allow
            # different things here. Some have the toggle on the Docket Report
            # page to allow headers, others do not. The ones that do not *seem*
            # to default to including the headers. There's also a setting in
            # ECF accounts that you can toggle to always include headers, but
            # it's entirely unclear how it interacts with the per-docket
            # settings. Anyway, we aggressively turn on the headers without an
            # option to turn them off atm.
            "pdf_header": "1",
            "pdf_toggle_possible": "1",
        }
        timeout = (60, 300)
        logger.info("POSTing URL: %s with params: %s" % (url, data))
        r = self.session.post(url, data=data, timeout=timeout)
        return r, url

    def download_pdf(self, pacer_case_id, pacer_doc_id):
        """Download a PDF from PACER.

        Note that this doesn't support attachments yet.

        :returns: request.Response object containing a PDF, if one can be found
        (is not sealed, gone, etc.). Else, returns None.
        """
        r, url = self._query_pdf_download(
            pacer_case_id, pacer_doc_id, got_receipt="1"
        )

        if u"This document is not available" in r.text:
            logger.error(
                "Document not available in case: %s at %s", url, pacer_case_id
            )
            return None
        if u"You do not have permission to view this document." in r.text:
            logger.warn(
                "Permission denied getting document %s in case %s. "
                "It's probably sealed.",
                pacer_case_id,
                url,
            )
            return None

        # Some pacer sites use window.location in their JS, so we have to look
        # for that. See: oknd, 13-cv-00357-JED-FHM, doc #24. But, be warned,
        # you can only catch the redirection with JS off.
        m = self.REDIRECT_REGEX.search(r.text)
        if m is not None:
            r = self.session.get(urljoin(url, m.group(1)))
            r.raise_for_status()

        # The request above sometimes generates an HTML page with an iframe
        # containing the PDF, and other times returns the PDF directly. ∴
        # either get the src of the iframe and download the PDF or just return
        # the pdf.
        r.raise_for_status()
        if is_pdf(r):
            logger.info("Got PDF binary data for case at %s", url)
            return r

        text = clean_html(r.text)
        tree = get_html_parsed_text(text)
        tree.rewrite_links(fix_links_in_lxml_tree, base_href=r.url)
        try:
            iframe_src = tree.xpath("//iframe/@src")[0]
        except IndexError:
            if "pdf:Producer" in text:
                logger.error(
                    "Unable to download PDF. PDF content was placed "
                    "directly in HTML. URL: %s, caseid: %s",
                    url,
                    pacer_case_id,
                )
            else:
                logger.error(
                    "Unable to download PDF. PDF not served as "
                    "binary data and unable to find iframe src "
                    "attribute. URL: %s, caseid: %s",
                    url,
                    pacer_case_id,
                )
            return None

        r = self.session.get(iframe_src)
        if is_pdf(r):
            logger.info(
                "Got iframed PDF data for case %s at: %s", url, iframe_src
            )

        return r

    def is_pdf_sealed(self, pacer_case_id, pacer_doc_id):
        """Check if a PDF is sealed without trying to actually download
        it.
        """
        r, url = self._query_pdf_download(
            pacer_case_id, pacer_doc_id, got_receipt="0"
        )
        sealed = "You do not have permission to view this document."
        return sealed in r.content
