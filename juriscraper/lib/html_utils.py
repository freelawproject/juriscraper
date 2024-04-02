#!/usr/bin/env python
import re
import sys
from copy import deepcopy
from urllib.parse import urlsplit, urlunsplit

import nh3
from lxml import etree, html
from lxml.html import HtmlElement, fromstring, tostring
from requests import Response

try:
    # Use charset-normalizer for performance to detect the character encoding.
    import charset_normalizer as chardet
except ImportError:
    import chardet

if sys.maxunicode == 65535:
    from .log_tools import make_default_logger

    logger = make_default_logger()
    logger.warning(
        "You are using a narrow build of Python, which is not "
        "completely supported. See issue #188 for details."
    )

ALLOWED_ATTRIBUTES = deepcopy(nh3.ALLOWED_ATTRIBUTES)
ALLOWED_ATTRIBUTES["a"].update({"id", "onclick"})
ALLOWED_ATTRIBUTES["div"] = {"class", "id"}
ALLOWED_ATTRIBUTES["font"] = {"face", "size"}
ALLOWED_ATTRIBUTES["form"] = {"name", "method", "action"}
ALLOWED_ATTRIBUTES["input"] = {"name", "value", "type", "onclick"}
ALLOWED_ATTRIBUTES["span"] = {"class"}
ALLOWED_ATTRIBUTES["table"].update({"border", "class"})
ALLOWED_ATTRIBUTES["tr"].add("class")

ALLOWED_TAGS = deepcopy(nh3.ALLOWED_TAGS)
ALLOWED_TAGS.add("font")
ALLOWED_TAGS.add("form")
ALLOWED_TAGS.add("input")
ALLOWED_TAGS.add("script")


def get_xml_parsed_text(text):
    return etree.fromstring(text)


def get_html_parsed_text(text):
    return html.fromstring(text)


def get_html_from_element(element):
    return tostring(element)


def get_html5_parsed_text(text: str) -> HtmlElement:
    """Return content using the html5parser, ideal for faulty html.

    This first uses nh3 to sanitize the html before parsing it with
    the usual lxml parser.

    :param text: The html of the document
    :return: an lxml.HtmlElement object
    """
    return fromstring(
        nh3.clean(
            text,
            strip_comments=False,
            attributes=ALLOWED_ATTRIBUTES,
            clean_content_tags=set(),
            tags=ALLOWED_TAGS,
        )
    )


def get_table_column_text(
    html: HtmlElement,
    cell_num: int,
    path_base: bool = False,
    table_id: str = "",
) -> list:
    table = f"table[@id='{table_id}']" if table_id else "table"
    path_cell = "//%s//tr/td[%d]" % (table, cell_num)
    path = path_base + path_cell if path_base else path_cell
    return [cell.text_content().strip() for cell in html.xpath(path)]


def get_table_column_links(
    html: HtmlElement,
    cell_num: int,
    path_base: bool = False,
    table_id: str = "",
) -> list:
    table = f"table[@id='{table_id}']" if table_id else "table"
    path_cell = "//%s//tr/td[%d]//a/@href" % (table, cell_num)
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


def strip_bad_html_tags_insecure(
    text: str, remove_scripts=True
) -> HtmlElement:
    """Remove bad HTML that isn't used by our parsers.

    This is insecure in the sense that it does not strip all JavaScript. lxml
    provides a `javascript` parameter that can be passed to the Cleaner object,
    but it will clean JS attributes off nodes, which we can't do because we
    parse those for useful data.

    :param text: The HTML str you wish to cleanup
    :param remove_scripts: Do we want to remove scripts
    :return: the cleaned HTML tree
    """

    assert isinstance(
        text, str
    ), f"`text` must be of type str, but is of type {type(text)}."

    clean_content_tags = {"style"}
    if remove_scripts:
        clean_content_tags.add("script")
        tags = deepcopy(ALLOWED_TAGS)
        tags.remove("script")
    else:
        tags = ALLOWED_TAGS

    return fromstring(
        nh3.clean(
            text,
            strip_comments=False,
            attributes=ALLOWED_ATTRIBUTES,
            clean_content_tags=clean_content_tags,
            tags=tags,
        )
    )


def get_visible_text(html_content):
    html_tree = html.fromstring(html_content)
    text = html_tree.xpath(
        """//text()[normalize-space() and not(parent::style |
                                                                 parent::link |
                                                                 parent::head |
                                                                 parent::script)]"""
    )
    return " ".join(text)


def set_response_encoding(request):
    """Set the encoding if it isn't set already.

    Use charset-normalizer for added performance.
    """
    if request:
        # If the encoding is iso-8859-1, switch it to cp1252 (a superset)
        if request.encoding == "ISO-8859-1":
            request.encoding = "cp1252"

        if request.encoding is None:
            # Requests detects the encoding when the item is GET'ed using
            # HTTP headers, and then when r.text is accessed, if the
            # encoding hasn't been set by that point. By setting the
            # encoding here, we ensure that it's done by charset-normalizer,
            # if it hasn't been done with HTTP headers. This way it is done
            # before r.text is accessed (which would do it with vanilla
            # chardet). This is a big performance boon, and can be removed
            # once requests is upgraded
            if isinstance(request.content, str):
                as_bytes = request.content.encode()
                request.encoding = chardet.detect(as_bytes)["encoding"]
            else:
                request.encoding = chardet.detect(request.content)["encoding"]


def clean_html(text: str) -> str:
    """Cleans up text before we make it into an HTML tree:
    1. Nukes <![CDATA stuff.
    2. Nukes XML encoding declarations
    3. Replaces </br> with <br/>
    4. Nukes invalid bytes in input
    5. ?
    """
    # Remove <![CDATA because it causes breakage in lxml.
    text = re.sub(r"<!\[CDATA\[", "", text)
    text = re.sub(r"\]\]>", "", text)

    # Remove <?xml> declaration in Unicode objects, because it causes an
    # error: "ValueError: Unicode strings with encoding declaration are not
    # supported."
    # Note that the error only occurs if the <?xml> tag has an "encoding"
    # attribute, but we remove it in all cases, as there's no downside to
    # removing it. This moves our encoding detection to chardet, rather than
    # lxml.
    if isinstance(text, str):
        text = re.sub(r"^\s*<\?xml\s+.*?\?>", "", text)

        # Remove bad escaped HTML chars &#01 or &#1 to &#08 or &#8 since are not
        # valid XML bytes 0x1 to 0x8
        text = re.sub(r"&#0[1-8]\b|&#[1-8]\b", "", text)

    # Fix invalid bytes in XML (http://stackoverflow.com/questions/8733233/)
    # Note that this won't work completely on narrow builds of Python, which
    # existed prior to Py3. Thus, we check if it's a narrow build, and adjust
    # accordingly.
    if sys.maxunicode == 65535:
        text = re.sub(
            "[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD]+", "", text
        )
    else:
        text = re.sub(
            "[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD"
            "\U00010000-\U0010FFFF]+",
            "",
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
        + (re.sub(r"^(/\.\.)+", "", url_parts.path),)
        + url_parts[3:]
    )
    if keep_anchors:
        return url
    else:
        return url.split("#")[0]


def is_html(response: Response) -> bool:
    """Determines whether the item downloaded is an HTML document or something
    else."""
    if "text/html" in response.headers.get("content-type", ""):
        return True
    return False
