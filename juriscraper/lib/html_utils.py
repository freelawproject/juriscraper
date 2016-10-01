#!/usr/bin/env python
# encoding: utf-8

from lxml import html
from lxml.html.clean import Cleaner
from lxml.etree import XMLSyntaxError
from lxml.html import html5parser, fromstring, tostring


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
    return fromstring(tostring(parsed))


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
