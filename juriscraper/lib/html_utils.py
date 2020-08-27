#!/usr/bin/env python
# encoding: utf-8
import re
import sys

import lxml
from lxml import etree, html
from lxml.etree import XMLSyntaxError
from lxml.html import fromstring, html5parser, tostring
from lxml.html.clean import Cleaner
from six import text_type
from six.moves.html_parser import HTMLParser
from six.moves.urllib.parse import urlsplit, urlunsplit

try:
    # Use cchardet for performance to detect the character encoding.
    import cchardet as chardet
except ImportError:
    import chardet

if sys.maxunicode == 65535:
    from .log_tools import make_default_logger

    logger = make_default_logger()
    logger.warn(
        "You are using a narrow build of Python, which is not "
        "completely supported. See issue #188 for details."
    )


def get_xml_parsed_text(text):
    return etree.fromstring(text)


def get_html_parsed_text(text):
    return html.fromstring(text)


def get_html_from_element(element):
    return tostring(element)


def get_html5_parsed_text(text):
    """Return content using the html5parser, ideal for faulty html.

    This dance is slightly different than usual because it uses the
    html5parser to first create an _Element object, then serialize it using
    `tostring`, then parse *that* using the usual fromstring function. The
    end result is that irregularities in the html are fixed by the
    html5parser, and the usual lxml parser gives us the same API we are
    used to.

    :param text: The html of the document
    :return: an lxml.HtmlElement object
    """
    parsed = html5parser.document_fromstring(text.encode("utf-8"))
    return fromstring(tostring(parsed, encoding="unicode"))


def get_table_column_text(html, cell_num, path_base=False):
    path_cell = "//table//tr/td[%d]" % cell_num
    path = path_base + path_cell if path_base else path_cell
    return [cell.text_content().strip() for cell in html.xpath(path)]


def get_table_column_links(html, cell_num, path_base=False):
    path_cell = "//table//tr/td[%d]//a/@href" % cell_num
    path = path_base + path_cell if path_base else path_cell
    return html.xpath(path)


def get_row_column_text(row, cell_num):
    """Return string cell value for specified column.

    :param row: HtmlElement
    :param cell_num: int
    :return: string
    """
    return row.xpath(".//td[%d]" % cell_num)[0].text_content().strip()


def get_row_column_links(row, cell_num):
    """Return string href value for link in specified column.

    NOTE: if there are multiple links in the column, you might
    need to write your own function.

    :param row: HtmlElement
    :param cell_num: int
    :return: string
    """
    return row.xpath(".//td[%d]//a/@href" % cell_num)[0]


def get_clean_body_content(content, remove_extra_tags=[]):
    """Parse out the body from an html string, clean it up, and send it along."""
    remove_tags = ["a", "body", "font", "noscript"]
    remove_tags.extend(remove_extra_tags)
    cleaner = Cleaner(style=True, remove_tags=remove_tags)
    try:
        return cleaner.clean_html(content)
    except XMLSyntaxError:
        return (
            "Unable to extract the content from this file. Please try "
            "reading the original."
        )


def strip_bad_html_tags_insecure(tree):
    """Remove bad HTML that isn't used by our parsers.

    This is insecure in the sense that it does not strip all JavaScript. lxml
    provides a `javascript` parameter that can be passed to the Cleaner object,
    but it will clean JS attributes off nodes, which we can't do because we
    parse those for useful data.

    :param tree: A tree you wish to cleanup
    :type tree: lxml.html.HtmlElement
    :return the cleaned HTML str
    """
    assert isinstance(tree, lxml.html.HtmlElement), (
        "`tree` must be of type HtmlElement, but is of type %s. Cleaner() can "
        "work with strs and unicode, but it does bad things to encodings if "
        "given the chance." % type(tree)
    )
    cleaner = Cleaner(
        # Keep JS: We parse onclicks for pacer metadata
        javascript=False,
        safe_attrs_only=False,
        # Keep forms: We parse them for metadata
        forms=False,
        # Keep comments: We use them in appellate PACER. For discussion and fix
        # to funky workaround below, see:
        #   https://bugs.launchpad.net/lxml/+bug/1882606
        # This workaround can be removed once lxml 4.5.2 is released
        comments=False,
        processing_instructions=False,
        remove_unknown_tags=False,
        allow_tags=set(lxml.html.defs.tags) | {lxml.etree.Comment},
        # Things we *can* actually remove
        scripts=True,
        style=True,
        links=True,
        embedded=True,
        frames=True,
    )
    return cleaner.clean_html(tree)


def get_visible_text(html_content):
    html_tree = html.fromstring(html_content)
    text = html_tree.xpath(
        """//text()[normalize-space() and not(parent::style |
                                                                 parent::link |
                                                                 parent::head |
                                                                 parent::script)]"""
    )
    return " ".join(text)


def html_unescape(s):
    h = HTMLParser()
    return h.unescape(s)


def set_response_encoding(request):
    """Set the encoding if it isn't set already.

    Use cchardet for added performance.
    """
    if request:
        # If the encoding is iso-8859-1, switch it to cp1252 (a superset)
        if request.encoding == "ISO-8859-1":
            request.encoding = "cp1252"

        if request.encoding is None:
            # Requests detects the encoding when the item is GET'ed using
            # HTTP headers, and then when r.text is accessed, if the encoding
            # hasn't been set by that point. By setting the encoding here, we
            # ensure that it's done by cchardet, if it hasn't been done with
            # HTTP headers. This way it is done before r.text is accessed
            # (which would do it with vanilla chardet). This is a big
            # performance boon, and can be removed once requests is upgraded
            if isinstance(request.content, text_type):
                as_bytes = request.content.encode()
                request.encoding = chardet.detect(as_bytes)["encoding"]
            else:
                request.encoding = chardet.detect(request.content)["encoding"]


def clean_html(text):
    """Cleans up text before we make it into an HTML tree:
    1. Nukes <![CDATA stuff.
    2. Nukes XML encoding declarations
    3. Replaces </br> with <br/>
    4. Nukes invalid bytes in input
    5. ?
    """
    # Remove <![CDATA because it causes breakage in lxml.
    text = re.sub(r"<!\[CDATA\[", u"", text)
    text = re.sub(r"\]\]>", u"", text)

    # Remove <?xml> declaration in Unicode objects, because it causes an
    # error: "ValueError: Unicode strings with encoding declaration are not
    # supported."
    # Note that the error only occurs if the <?xml> tag has an "encoding"
    # attribute, but we remove it in all cases, as there's no downside to
    # removing it. This moves our encoding detection to chardet, rather than
    # lxml.
    if isinstance(text, text_type):
        text = re.sub(r"^\s*<\?xml\s+.*?\?>", "", text)

    # Fix invalid bytes in XML (http://stackoverflow.com/questions/8733233/)
    # Note that this won't work completely on narrow builds of Python, which
    # existed prior to Py3. Thus, we check if it's a narrow build, and adjust
    # accordingly.
    if sys.maxunicode == 65535:
        text = re.sub(
            u"[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD]+", u"", text
        )
    else:
        text = re.sub(
            u"[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD"
            u"\U00010000-\U0010FFFF]+",
            u"",
            text,
        )

    return text


def fix_links_but_keep_anchors(link):
    # Wrap the function below so that we have one that can be passed to
    # lxml's rewrite_links method, which doesn't accept any parameters.
    return fix_links_in_lxml_tree(link, keep_anchors=True)


def fix_links_in_lxml_tree(link, keep_anchors=False):
    """Fix links in an lxml tree.

    :param keep_anchors: Whether to nuke anchors at the ends of links.

    This function is called by the rewrite_links method of an lxml tree, and is
    used to normalize links in a few ways. It makes links absolute, works
    around buggy URLs and nukes anchors.

    Example: html_tree.rewrite_links(fix_links_in_lxml_tree, base_href=my_url)

    Some URLS, like the following, make no sense:
     - https://www.appeals2.az.gov/../Decisions/CR20130096OPN.pdf.
                                  ^^^^ -- This makes no sense!
    The fix is to remove any extra '/..' patterns at the beginning of the
    path.

    Others have annoying anchors on the end, like:
     - http://example.com/path/#anchor

    Note that lxml has a method generally for this purpose called
    make_links_absolute, but we cannot use it because it does not work
    around invalid relative URLS, nor remove anchors. This is a limitation
    of Python's urljoin that will be fixed in Python 3.5 according to a bug
    we filed: http://bugs.python.org/issue22118
    """
    url_parts = urlsplit(link)
    url = urlunsplit(
        url_parts[:2]
        + (re.sub("^(/\.\.)+", "", url_parts.path),)
        + url_parts[3:]
    )
    if keep_anchors:
        return url
    else:
        return url.split("#")[0]
