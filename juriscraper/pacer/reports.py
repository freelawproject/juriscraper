import re
from typing import Optional, Tuple
from urllib.parse import urljoin

import requests
from lxml.html import HtmlElement
from requests import Response

from ..lib.html_utils import (
    clean_html,
    fix_links_in_lxml_tree,
    get_html5_parsed_text,
    get_html_parsed_text,
    is_html,
    set_response_encoding,
    strip_bad_html_tags_insecure,
)
from ..lib.log_tools import make_default_logger
from .utils import is_pdf, make_doc1_url, make_docs1_url

logger = make_default_logger()


# Patch the HtmlElement class to add a function that can handle regular
# expressions within XPath queries. See usages throughout AppellateDocketReport.
def re_xpath(self, path):
    return self.xpath(
        path, namespaces={"re": "http://exslt.org/regular-expressions"}
    )


HtmlElement.re_xpath = re_xpath


class BaseReport:
    """A base report for working with pages on PACER."""

    # Subclasses should override PATH
    PATH = ""

    # Strings below (and in subclasses) are used to identify HTML that should
    # not be parsed or processed for a variety of reasons. Spaces in the
    # strings below are converted to \s whitespace searches using regexes.
    ERROR_STRINGS = [
        "MetaMask.*web3",
        r'console\.log\(".*CloudMask',
        "Drumpf",
    ]

    def __init__(self, court_id, pacer_session=None):
        self.court_id = court_id
        self.session = pacer_session
        self.tree = None
        self.response = None
        self.is_valid = None

    @property
    def url(self):
        if self.court_id == "psc":
            return f"https://dcecf.psc.uscourts.gov/{self.PATH}"
        else:
            return f"https://ecf.{self.court_id}.uscourts.gov/{self.PATH}"

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
            text, str
        ), f"Input must be unicode, not {type(text)}"
        text = clean_html(text)
        self.check_validity(text)
        if self.is_valid:
            tree = get_html5_parsed_text(text)
            self.tree = strip_bad_html_tags_insecure(tree)
            self.tree.rewrite_links(fix_links_in_lxml_tree, base_href=self.url)

    def check_validity(self, text: str) -> None:
        """Place sanity checks here to make sure that the returned text is
        valid and not an error page or some other kind of problem.

        Set self.is_valid flag to True or False
        """
        for error_string in self.ERROR_STRINGS:
            error_string_re = re.compile(
                r"\s+".join(error_string.split()), flags=re.I
            )
            if error_string_re.search(text):
                self.is_valid = False
                return
        self.is_valid = True

    @property
    def data(self):
        """Extract the data from the tree and return it."""
        raise NotImplementedError(".data() must be overridden.")

    def _query_pdf_download(
        self,
        pacer_case_id: str,
        pacer_doc_id: str,
        pacer_magic_num: Optional[str],
        got_receipt: str,
    ) -> Tuple[Response, str]:
        """Query the doc1 download URL.

        :param pacer_case_id: The ID of the case
        :param pacer_doc_id: The doc id for the document
        :param got_receipt: Whether to get the receipt for the page ('0') or
        get the PDF itself ('1').
        :return the Request.response object and the url queried
        """
        url = make_doc1_url(self.court_id, pacer_doc_id, True)
        data = {
            # Sending the case ID is important if you want to get PDF headers.
            # Without the case ID, PACER won't know what case it is, and won't
            # be able to add the correct headers. That'd suggest that the case
            # ID should always be sent. Unfortunately though, in many criminal
            # cases, there are documents from other related cases, and at least
            # in CourtListener, we do a bad job of keeping track of which doc
            # is from which related criminal case. If you send the *wrong* case
            # ID, you get no document at all. Though you do get a useful error
            # message. As a result, the approach we take in self.download_pdf
            # is to try it with the case ID, and then if we see that error
            # message, we try it again without the case ID. We won't get the
            # headers in that case, but we'll at least get the document.
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

        # This is not always set, so we give it an option here.
        if pacer_magic_num is not None:
            data["magic_num"] = pacer_magic_num

        timeout = (60, 300)
        logger.info(f"POSTing URL: {url} with params: {data}")
        r = self.session.post(url, data=data, timeout=timeout)
        return r, url

    def download_pdf(
        self,
        pacer_case_id: str,
        pacer_doc_id: int,
        pacer_magic_num: Optional[str] = None,
        appellate: bool = False,
    ) -> Tuple[Optional[Response], str]:
        """Download a PDF from PACER.

        Note that this doesn't support attachments yet.

        :returns: A tuple of the request.Response object containing a PDF, if
        one can be found (is not sealed, gone, etc.). And a string indicating
        the error message, if there is one or else an empty string.
        """
        if pacer_magic_num:
            # If magic_number is available try to download the
            # document anonymously by its magic link

            # Create PACER base url from court_id and pacer_doc_id
            # Magic link parameters
            # We don't need the de_seq_num parameter to fetch the free document
            if appellate:
                url = make_docs1_url(self.court_id, pacer_doc_id, True)
                # For appellate documents the magic_number is the uid param
                params = {
                    "uid": pacer_magic_num,
                }
            else:
                url = make_doc1_url(self.court_id, pacer_doc_id, True)
                params = {
                    "caseid": pacer_case_id,
                    "magic_num": pacer_magic_num,
                }

            # Add parameters to the PACER base url and make a GET request
            req_timeout = (60, 300)
            r = requests.get(url, params=params, timeout=req_timeout)

            # If the response is an HTML document, and it doesn't contain an
            # IFRAME, the magic link document is no longer available
            error = None
            if is_html(r) and "iframe" not in r.text:
                error = (
                    f"Document not available via magic link in case: "
                    f"caseid: {pacer_case_id}, magic_num: {pacer_magic_num}, "
                    f"URL: {url}"
                )
            if error:
                logger.warning(error)
                return None, error

        else:
            # If no magic_number use normal method to fetch the document
            r, url = self._query_pdf_download(
                pacer_case_id, pacer_doc_id, pacer_magic_num, got_receipt="1"
            )

            # Use r.content instead of r.text for performance. See #564
            if b"Cannot locate the case with caseid" in r.content:
                # This document is from a different docket, but is included in
                # this docket. Probably a criminal case with the doppelganger
                # bug. Try again, but do so without the pacer_case_id.
                # This should work, but will omit the blue header on the PDFs.
                r, url = self._query_pdf_download(
                    None, pacer_doc_id, pacer_magic_num, got_receipt="1"
                )

            error = None
            if b"could not retrieve dktentry for dlsid" in r.content:
                error = (
                    f"Failed to get docket entry in case: "
                    f"{pacer_case_id=} at {url}"
                )
            if b"document is not available" in r.content:
                # See: https://ecf.akb.uscourts.gov/doc1/02211536343
                # See: https://ecf.ksd.uscourts.gov/doc1/07912639735
                # Matches against:
                # "The document is not available" and
                # "This document is not available"
                error = (
                    f"Document not available in case: "
                    f"{pacer_case_id=} at {url}"
                )
            if re.search(
                rb"You do not have permission to view\s+this document.",
                r.content,
            ):
                error = (
                    f"Permission denied getting document. It's probably "
                    f"sealed. {pacer_case_id=}, {url=}"
                )
            if b"You do not have access to this transcript." in r.content:
                error = f"Unable to get transcript. {pacer_case_id=}, {url=}"
            if b"Sealed Document" in r.content or b"Under Seal" in r.content:
                # See: https://ecf.almd.uscourts.gov/doc1/01712589088
                # See: https://ecf.cand.uscourts.gov/doc1/035122021132
                # Matches against:
                # "Sealed Document" and
                # "This document is currently Under Seal and not available..."
                error = f"Document is sealed: {pacer_case_id=} {url=}"
            if (
                b"This image is not available for viewing by non-court users"
                in r.content
            ):
                # See: https://ecf.wvsd.uscourts.gov/doc1/20115419289
                error = (
                    f"Image not available for viewing by non-court users. "
                    f"{pacer_case_id=}, {url=}"
                )
            if b"A Client Code is required for PACER search" in r.content:
                error = (
                    f"Unable to get document. Client code required: "
                    f"{pacer_case_id=}, {url=}"
                )
            if (
                b"Permission to view this document is denied based on Nature of Suit"
                in r.content
            ):
                # See: https://ecf.cacd.uscourts.gov/doc1/031134206600
                error = (
                    f"Permission denied getting document due to nature of "
                    f"suit. {pacer_case_id=}, {url=}"
                )

            if error:
                logger.warning(error)
                return None, error

            # Some pacer sites use window.location in their JS, so we have to
            # look for that. See: oknd, 13-cv-00357-JED-FHM, doc #24. But, be
            # warned, you can only catch the redirection with JS off.
            redirect_re = re.compile(rb'window\.\s*?location\s*=\s*"(.*)"\s*;')
            m = redirect_re.search(r.content)
            if m is not None:
                r = self.session.get(urljoin(url, str(m.group(1))))
                r.raise_for_status()

        # The request above sometimes generates an HTML page with an iframe
        # containing the PDF, and other times returns the PDF directly. ∴
        # either get the src of the iframe and download the PDF or just return
        # the pdf.
        r.raise_for_status()
        if is_pdf(r):
            logger.info(f"Got PDF binary data for case at {url}")
            return r, ""

        text = clean_html(r.text)
        tree = get_html_parsed_text(text)
        tree.rewrite_links(fix_links_in_lxml_tree, base_href=r.url)
        try:
            iframe_src = tree.xpath("//iframe/@src")[0]
        except IndexError:
            if "pdf:Producer" in text:
                error = (
                    "Unable to download PDF. PDF content was placed "
                    f"directly in HTML. URL: {url}, caseid: {pacer_case_id}, "
                    f"magic_num: {pacer_magic_num}"
                )
            else:
                error = (
                    "Unable to download PDF. PDF not served as "
                    "binary data and unable to find iframe src "
                    f"attribute. URL: {url}, caseid: {pacer_case_id}, "
                    f"magic_num: {pacer_magic_num}"
                )
            logger.error(error)
            return None, error

        if pacer_magic_num:
            # If magic_number is available try to download the
            # document anonymously from iframe_src
            r = requests.get(iframe_src, timeout=req_timeout)
        else:
            # Use PACER session to fetch the document from iframe_src
            r = self.session.get(iframe_src)
        if is_pdf(r):
            logger.info(
                f"Got iframed PDF data for case {url} at: {iframe_src}"
            )

        return r, ""

    def is_pdf_sealed(self, pacer_case_id, pacer_doc_id, pacer_magic_num=None):
        """Check if a PDF is sealed without trying to actually download
        it.
        """
        r, url = self._query_pdf_download(
            pacer_case_id, pacer_doc_id, pacer_magic_num, got_receipt="0"
        )
        sealed = "You do not have permission to view this document."
        return sealed in r.content
