#!/usr/bin/env python
# encoding: utf-8

from lxml import html

def get_visible_text(html_content):
    html_tree = html.fromstring(html_content)
    text = html_tree.xpath("""//text()[normalize-space() and not(parent::style | 
                                                                 parent::link | 
                                                                 parent::head | 
                                                                 parent::script)]""")
    return " ".join(text)
