#!/usr/bin/env python
# encoding: utf-8
import re
import sys

from lxml import html
from lxml.etree import XMLSyntaxError
from lxml.html import html5parser, fromstring, tostring
from lxml.html.clean import Cleaner
from six import text_type
from six.moves.urllib.parse import urlsplit, urlunsplit

try:
    # Use cchardet for performance to detect the character encoding.
    import cchardet as chardet
except ImportError:
    import chardet

if sys.maxunicode == 65535:
    from .log_tools import make_default_logger
    logger = make_default_logger()
    logger.warn("You are using a narrow build of Python, which is not "
                "completely supported. See issue #188 for details.")


def get_html_parsed_text(text):
    return html.fromstring(text)


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
    parsed = html5parser.document_fromstring(text.encode('utf-8'))
    return fromstring(tostring(parsed, encoding='unicode'))


def get_clean_body_content(content, remove_extra_tags=[]):
    """Parse out the body from an html string, clean it up, and send it along.
    """
    remove_tags = ['a', 'body', 'font', 'noscript']
    remove_tags.extend(remove_extra_tags)
    cleaner = Cleaner(style=True,
                      remove_tags=remove_tags)
    try:
        return cleaner.clean_html(content)
    except XMLSyntaxError:
        return "Unable to extract the content from this file. Please try " \
               "reading the original."


def get_visible_text(html_content):
    html_tree = html.fromstring(html_content)
    text = html_tree.xpath("""//text()[normalize-space() and not(parent::style |
                                                                 parent::link |
                                                                 parent::head |
                                                                 parent::script)]""")
    return " ".join(text)


def set_response_encoding(request):
    """Set the encoding if it isn't set already.

    Use cchardet for added performance.
    """
    if request:
        # If the encoding is iso-8859-1, switch it to cp1252 (a superset)
        if request.encoding == 'ISO-8859-1':
            request.encoding = 'cp1252'

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
                request.encoding = chardet.detect(as_bytes)['encoding']
            else:
                request.encoding = chardet.detect(request.content)['encoding']


def clean_html(text):
    """ Cleans up text before we make it into an HTML tree:
        1. Nukes <![CDATA stuff.
        2. Nukes XML encoding declarations
        3. Replaces </br> with <br/>
        4. Nukes invalid bytes in input
        5. ?
    """
    # Remove <![CDATA because it causes breakage in lxml.
    text = re.sub(r'<!\[CDATA\[', u'', text)
    text = re.sub(r'\]\]>', u'', text)

    # Remove <?xml> declaration in Unicode objects, because it causes an
    # error: "ValueError: Unicode strings with encoding declaration are not
    # supported."
    # Note that the error only occurs if the <?xml> tag has an "encoding"
    # attribute, but we remove it in all cases, as there's no downside to
    # removing it. This moves our encoding detection to chardet, rather than
    # lxml.
    if isinstance(text, text_type):
        text = re.sub(r'^\s*<\?xml\s+.*?\?>', '', text)

    # Fix </br>
    text = re.sub('</br>', '<br/>', text)

    # Fix invalid bytes in XML (http://stackoverflow.com/questions/8733233/)
    # Note that this won't work completely on narrow builds of Python, which
    # existed prior to Py3. Thus, we check if it's a narrow build, and adjust
    # accordingly.
    if sys.maxunicode == 65535:
        text = re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD]+',
                      u'', text)
    else:
        text = re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD'
                      u'\U00010000-\U0010FFFF]+', u'', text)

    return text


def fix_links_in_lxml_tree(link):
    """Fix links in an lxml tree.

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
        url_parts[:2] +
        (re.sub('^(/\.\.)+', '', url_parts.path),) +
        url_parts[3:]
    )
    return url.split('#')[0]
