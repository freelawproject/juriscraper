#!/usr/bin/env python
# encoding: utf-8

from lxml import html
from lxml.etree import XMLSyntaxError
from lxml.html.clean import Cleaner


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
