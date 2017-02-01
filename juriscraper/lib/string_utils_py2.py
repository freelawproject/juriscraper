# -*- coding: utf-8 -*-
"""
Python 2.x Regular Express patterns for string_utils.py
"""
import re

BIG = ('3D|AFL|AKA|A/K/A|BMG|CBS|CDC|CDT|CEO|CIO|CNMI|D/B/A|DOJ|DVA|EFF|FCC|'
           'FTC|HSBC|IBM|II|III|IV|JJ|LLC|LLP|MCI|MJL|MSPB|ND|NLRB|PTO|SD|UPS|RSS|SEC|UMG|US|USA|USC|'
           'USPS|WTO')
SMALL = u'a|an|and|as|at|but|by|en|for|if|in|is|of|on|or|the|to|v\.?|via|vs\.?'
NUMS = u'0123456789'
PUNCT = ur"""!"#$¢%&'‘()*+,\-./:;?@[\\\]_—`{|}~"""
WEIRD_CHARS = ur'¼½¾§ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜßàáâãäåæçèéêëìíîïñòóôœõöøùúûüÿ'
BIG_WORDS = re.compile(ur'^(%s)[%s]?$' % (BIG, PUNCT), re.I | re.U)
SMALL_WORDS = re.compile(r'^(%s)$' % SMALL, re.I)
SMALL_WORD_INLINE = re.compile(r'(^|\s)(%s)(\s|$)' % SMALL, re.I | re.U)
INLINE_PERIOD = re.compile(r'[a-z][.][a-z]', re.I)
INLINE_SLASH = re.compile(r'[a-z][/][a-z]', re.I)
INLINE_AMPERSAND = re.compile(r'([a-z][&][a-z])(.*)', re.I)
UC_ELSEWHERE = re.compile(ur'[%s]*?[a-zA-Z]+[A-Z]+?' % PUNCT, re.U)
CAPFIRST = re.compile(ur"^[%s]*?([A-Za-z])" % PUNCT)
SMALL_FIRST = re.compile(ur'^([%s]*)(%s)\b' % (PUNCT, SMALL), re.I | re.U)
SMALL_LAST = re.compile(r'\b(%s)[%s]?$' % (SMALL, PUNCT), re.I | re.U)
SUBPHRASE = re.compile(r'([:;?!][ ])(%s)' % SMALL)
APOS_SECOND = re.compile(r"^[dol]{1}['‘]{1}[a-z]+$", re.I)
ALL_CAPS = re.compile(ur'^[A-Z\s%s%s%s]+$' % (PUNCT, WEIRD_CHARS, NUMS))
UC_INITIALS = re.compile(r"^(?:[A-Z]{1}\.{1}|[A-Z]{1}\.{1}[A-Z]{1})+,?$")
MAC_MC = re.compile(r'^([Mm]a?c)(\w+.*)')