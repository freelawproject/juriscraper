# -*- coding: utf-8 -*-
import re

# For use in titlecase
BIG = ('3D|AFL|AKA|A/K/A|BMG|CBS|CDC|CDT|CEO|CIO|CNMI|D/B/A|DOJ|DVA|EFF|FCC|'
       'FTC|HSBC|IBM|II|III|IV|JJ|LLC|LLP|MCI|MJL|MSPB|ND|NLRB|PTO|SD|UPS|RSS|SEC|UMG|US|USA|USC|'
       'USPS|WTO')
SMALL = 'a|an|and|as|at|but|by|en|for|if|in|is|of|on|or|the|to|v\.?|via|vs\.?'
NUMS = '0123456789'
PUNCT = r"""!"#$¢%&'‘()*+,\-./:;?@[\\\]_—`{|}~"""
WEIRD_CHARS = r'¼½¾§ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜßàáâãäåæçèéêëìíîïñòóôœõöøùúûüÿ'
BIG_WORDS = re.compile(r'^(%s)[%s]?$' % (BIG, PUNCT), re.I)
SMALL_WORDS = re.compile(r'^(%s)$' % SMALL, re.I)
SMALL_WORD_INLINE = re.compile(r'(^|\s)(%s)(\s|$)' % SMALL, re.I)
INLINE_PERIOD = re.compile(r'[a-z][.][a-z]', re.I)
INLINE_SLASH = re.compile(r'[a-z][/][a-z]', re.I)
INLINE_AMPERSAND = re.compile(r'([a-z][&][a-z])(.*)', re.I)
UC_ELSEWHERE = re.compile(r'[%s]*?[a-zA-Z]+[A-Z]+?' % PUNCT)
CAPFIRST = re.compile(r"^[%s]*?([A-Za-z])" % PUNCT)
SMALL_FIRST = re.compile(r'^([%s]*)(%s)\b' % (PUNCT, SMALL), re.I)
SMALL_LAST = re.compile(r'\b(%s)[%s]?$' % (SMALL, PUNCT), re.I)
SUBPHRASE = re.compile(r'([:;?!][ ])(%s)' % SMALL)
APOS_SECOND = re.compile(r"^[dol]{1}['‘]{1}[a-z]+$", re.I)
ALL_CAPS = re.compile(r'^[A-Z\s%s%s%s]+$' % (PUNCT, WEIRD_CHARS, NUMS))
UC_INITIALS = re.compile(r"^(?:[A-Z]{1}\.{1}|[A-Z]{1}\.{1}[A-Z]{1})+,?$")
MAC_MC = re.compile(r'^([Mm]a?c)(\w+.*)')
def titlecase(text, DEBUG=False):
    """Titlecases input text

    This filter changes all words to Title Caps, and attempts to be clever
    about *un*capitalizing SMALL words like a/an/the in the input.

    The list of "SMALL words" which are not capped comes from
    the New York Times Manual of Style, plus 'vs' and 'v'.

    This will fail if multiple sentences are provided as input and if the
    first word of a sentence is a SMALL_WORD.

    List of "BIG words" grows over time as entries are needed.
    """
    text_sans_small_words = re.sub(SMALL_WORD_INLINE, '', text)
    if text_sans_small_words.isupper():
        # if, after removing small words, the entire string is uppercase,
        # we lowercase it
        if DEBUG:
            print "Entire string is uppercase, thus lowercasing."
        text = text.lower()
    elif not text_sans_small_words.isupper() and DEBUG:
        print "Entire string not upper case. Not lowercasing: %s" % text

    lines = re.split('[\r\n]+', text)
    processed = []
    for line in lines:
        all_caps = ALL_CAPS.match(line)
        words = re.split('[\t ]', line)
        tc_line = []
        for word in words:
            if DEBUG:
                print "Word: " + word
            if all_caps:
                if UC_INITIALS.match(word):
                    if DEBUG:
                        print "  UC_INITIALS match for: " + word
                    tc_line.append(word)
                    continue
                else:
                    if DEBUG:
                        print "  Not initials. Lowercasing: " + word
                    word = word.lower()

            if APOS_SECOND.match(word):
                # O'Reiley, L'Oreal, D'Angelo
                if DEBUG:
                    print "  APOS_SECOND matched. Fixing it: " + word
                word = word[0:3].upper() + word[3:]
                tc_line.append(word)
                continue

            if INLINE_PERIOD.search(word):
                if DEBUG:
                    print "  INLINE_PERIOD matched. Uppercasing if == 1 char: " + word
                parts = word.split('.')
                new_parts = []
                for part in parts:
                    if len(part) == 1:
                        # It's an initial like U.S.
                        new_parts.append(part.upper())
                    else:
                        # It's something like '.com'
                        new_parts.append(part)
                word = '.'.join(new_parts)
                tc_line.append(word)
                continue

            if INLINE_SLASH.search(word):
                # This repeats INLINE_PERIOD. Could be more elegant.
                if DEBUG:
                    print "  INLINE_SLASH matched. Uppercasing if == 1 char: " + word
                parts = word.split('/')
                new_parts = []
                for part in parts:
                    if len(part) == 1:
                        # It's an initial like A/M
                        new_parts.append(part.upper())
                    else:
                        # It's something like 'True/False'
                        new_parts.append(part)
                word = '/'.join(new_parts)
                tc_line.append(word)
                continue

            amp_match = INLINE_AMPERSAND.match(word)
            if amp_match:
                if DEBUG:
                    print "  INLINE_AMPERSAND matched. Uppercasing: " + word
                tc_line.append("%s%s" % (amp_match.group(1).upper(),
                                         amp_match.group(2)))
                continue

            if UC_ELSEWHERE.match(word):
                if DEBUG:
                    print "  UC_ELSEWHERE matched. Leaving unchanged: " + word
                tc_line.append(word)
                continue

            if SMALL_WORDS.match(word):
                if DEBUG:
                    print "  SMALL_WORDS matched. Lowercasing: " + word
                tc_line.append(word.lower())
                continue

            if BIG_WORDS.match(word):
                if DEBUG:
                    print "  BIG_WORDS matched. Uppercasing: " + word
                tc_line.append(word.upper())
                continue

            match = MAC_MC.match(word)
            if match and (word not in ['mack', 'machine']):
                if DEBUG:
                    print "  MAC_MAC matched. Capitlizing: " + word
                tc_line.append("%s%s" % (match.group(1).capitalize(),
                                         match.group(2).capitalize()))
                continue

            hyphenated = []
            for item in word.split('-'):
                hyphenated.append(CAPFIRST.sub(lambda m: m.group(0).upper(), item))
            tc_line.append("-".join(hyphenated))

        result = " ".join(tc_line)

        result = SMALL_FIRST.sub(lambda m: '%s%s' % (
            m.group(1),
            m.group(2).capitalize()), result)

        result = SMALL_LAST.sub(lambda m: m.group(0).capitalize(), result)
        result = SUBPHRASE.sub(lambda m: '%s%s' % (
            m.group(1),
            m.group(2).capitalize()), result)

        processed.append(result)
        text = "\n".join(processed)

    # replace V. with v.
    text = re.sub(re.compile(r'\WV\.\W'), ' v. ', text)

    return text


def fix_camel_case(s):
    """Sometimes courts provide nasty camel-cased content instead of real
    words. This code attempts to fix that."""
    if ' ' in s:
        s_out = s
    else:
        s_out = s[0]
        for i in xrange(1, len(s)):
            # Iterate over the letters, starting with the second one.
            if s[i - 1].isupper() and s[i].isupper():
                # A pattern like 'PAPublic' --> PA Public
                try:
                    next_letter_is_lower = s[i + 1].islower() and s[i+1] != 'v'
                except IndexError:
                    # End of string. Break.
                    s_out += s[i]
                    continue
                if next_letter_is_lower:
                    s_out += ' %s' % s[i]
                else:
                    s_out += s[i]
            elif s[i - 1].islower() and s[i].isupper():
                # A pattern like 'McLaughlin'
                try:
                    mac_or_mc = ((s[i - 2] == 'a' and s[i - 3] == 'M') or
                                 s[i - 2] == 'M')
                except KeyError:
                    s_out += ' %s' % s[i]
                if s[i - 1] == 'c' and mac_or_mc:
                    s_out += s[i]
                else:
                    s_out += ' %s' % s[i]
            elif s[i].isupper() and s[i-1].islower():
                # Uppercase letter preceded by a lowercase one. Add a space then the letter.
                s_out += ' %s' % s[i]
            else:
                s_out += s[i]
        # Fix v.'s that don't have spaces. These come in two forms:
        # 1. So and sov.so and so
        s_out = ' '.join(re.sub('v\.', ' v. ', s_out).split())
        # 2. So and sov so and so --> So and so v. so and so
        if 'v.' not in s_out:
            s_out = ' '.join(re.sub('([^ ])v ', r'\1 v. ', s_out).split())

        # Fix strings like Governorof, Stateof, Secretaryofthe
        if 'of' in s_out:
            s_out = re.sub(r'([a-zA-Z])of( |(?:the))', r'\1 of\2', s_out)
        if 'the' in s_out:
            s_out = re.sub(r'([a-zA-Z])the ', r'\1 the ', s_out)

        # Fix strings like Santomenno,etal v. John Hancock Life Ins
        if 'etal' in s_out:
            s_out = re.sub(r',?etal( |\Z)', ' ', s_out).strip()

        # Fix strings like Inre SCH Corp v. CFI Class
        if 'Inre' in s_out:
            s_out = re.sub(r'^Inre ', 'In Re ', s_out)

    return s_out


# For use in harmonize function
# More details: http://www.law.cornell.edu/citation/4-300.htm
US = 'USA|U\.S\.A\.|U\.S\.?|U\. S\.?|(The )?United States of America|The United States'
UNITED_STATES = re.compile(r'^(%s)(,|\.)?$' % US, re.I)
THE_STATE = re.compile(r'the state', re.I)
ET_AL = re.compile(',?\set\.?\sal\.?', re.I)
BW = 'appell(ee|ant)s?|claimants?|complainants?|defendants?|defendants?(--?|/)appell(ee|ant)s?' + \
     '|devisee|executor|executrix|pet(\.|itioner)s?|petitioners?(--?|/)appell(ee|ant)s?' + \
     '|petitioners?(--?|/)defendants?|plaintiffs?|plaintiffs?(--?|/)appell(ee|ant)s?|respond(e|a)nts?' + \
     '|respond(e|a)nts?(--?|/)appell(ee|ant)s?|cross(--?|/)respondents?|crosss?(--?|/)petitioners?' + \
     '|cross(--?|/)appell(ees|ant)s?|deceased'
BAD_WORDS = re.compile(r'^(%s)(,|\.)?$' % BW, re.I)
def harmonize(text):
    """Fixes case names so they are cleaner.

    Using a bunch of regex's, this function cleans up common data problems in
    case names. The following are currently fixed:
     - various forms of United States --> United States
     - The State --> State
     - vs. --> v.
     - et al --> Removed.
     - plaintiff, appellee, defendant and the like --> Removed.
     - No. and Nos. removed from beginning

    Lots of tests are in tests.py.
    """

    result = ''
    # replace vs. with v.
    text = re.sub(re.compile(r'\Wvs\.\W'), ' v. ', text)

    # replace V. with v.
    text = re.sub(re.compile(r'\WV\.\W'), ' v. ', text)

    # replace v with v.
    text = re.sub(re.compile(r' v '), ' v. ', text)

    # and finally, vs with v.
    text = re.sub(re.compile(r' vs '), ' v. ', text)

    # Remove the BAD_WORDS.
    text = text.split()
    cleaned_text = []
    for word in text:
        word = re.sub(BAD_WORDS, '', word)
        cleaned_text.append(word)
    text = ' '.join(cleaned_text)

    # split on all ' v. ' and then deal with United States variations.
    text = text.split(' v. ')
    i = 1
    for frag in text:
        frag = frag.strip()
        if UNITED_STATES.match(frag):
            result += 'United States'
        elif THE_STATE.match(frag):
            result += 'State'
        else:
            # needed here, because we can't put "US" as a case-insensitive
            # word into the UNITED_STATES regex.
            frag = re.sub(re.compile(r'^US$'), 'United States', frag)
            # no match
            result += frag

        if i < len(text):
            # More stuff coming; append v.
            result += ' v. '
        i += 1

    # Remove the ET_AL words.
    result = re.sub(ET_AL, '', result)

    # Fix the No. and Nos.
    if result.startswith('No.') or result.startswith('Nos.'):
        result = re.sub(r'^Nos?\.\s+', '', result)

    return clean_string(result)


def clean_string(string):
    """Clean up strings.

    Accomplishes the following:
     - replaces HTML encoded characters with ASCII versions.
     - removes -, ' ', #, *, ; and ',' from the end of lines
     - converts to unicode.
     - removes weird white space and replaces with spaces.
    """
    # if not already unicode, make it unicode, dropping invalid characters
    # if not isinstance(string, unicode):
    string = force_unicode(string, errors='ignore')

    # Get rid of HTML encoded chars
    string = string.replace('&rsquo;', '\'').replace('&rdquo;', '\"')\
        .replace('&ldquo;', '\"').replace('&nbsp;', ' ')\
        .replace('&amp;', '&').replace('%20', ' ').replace('&#160;', ' ')

    # smart quotes
    string = string.replace(u'’', "'").replace(u'‘', "'").replace(u'“', '"')\
        .replace(u'”', '"')

    # Get rid of weird punctuation
    string = string.replace('*', '').replace('#', '').replace(';', '')

    # Strip bad stuff from the end of lines. Python's strip fails here because
    # we don't know the order of the various punctuation items to be stripped.
    # We split on the v., and handle fixes at either end of plaintiff or
    # appellant.
    bad_punctuation = u'(-|–|/|;|,|\s)*'
    bad_endings = re.compile(r'%s$' % bad_punctuation)
    bad_beginnings = re.compile(r'^%s' % bad_punctuation)

    string = string.split(' v. ')
    cleaned_string = []
    for frag in string:
        frag = re.sub(bad_endings, '', frag)
        frag = re.sub(bad_beginnings, '', frag)
        cleaned_string.append(frag)
    string = ' v. '.join(cleaned_string)

    # get rid of '\t\n\x0b\x0c\r ', and replace them with a single space.
    string = ' '.join(string.split())

    return string


def force_unicode(s, encoding='utf-8', strings_only=False, errors='strict'):
    # Borrows heavily from django.utils.encoding.force_unicde.
    # This should be applied to *input* not *output*!
    # Handle the common case first, saves 30-40% in performance when s
    # is an instance of unicode. This function gets called often in that
    # setting.
    if isinstance(s, unicode):
        return s
    try:
        if not isinstance(s, basestring,):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                try:
                    s = unicode(str(s), encoding, errors)
                except UnicodeEncodeError:
                    if not isinstance(s, Exception):
                        raise
                    # If we get to here, the caller has passed in an Exception
                    # subclass populated with non-ASCII data without special
                    # handling to display as a string. We need to handle this
                    # without raising a further exception. We do an
                    # approximation to what the Exception's standard str()
                    # output should be.
                    s = ' '.join([force_unicode(arg, encoding, strings_only,
                            errors) for arg in s])
        elif not isinstance(s, unicode):
            # Note: We use .decode() here, instead of unicode(s, encoding,
            # errors), so that if s is a SafeString, it ends up being a
            # SafeUnicode at the end.
            s = s.decode(encoding, errors)
    except UnicodeDecodeError, e:
        if not isinstance(s, Exception):
            raise
        else:
            # If we get to here, the caller has passed in an Exception
            # subclass populated with non-ASCII bytestring data without a
            # working unicode method. Try to handle this without raising a
            # further exception by individually forcing the exception args
            # to unicode.
            s = ' '.join([force_unicode(arg, encoding, strings_only,
                    errors) for arg in s])
    return s


def trunc(s, length, ellipsis=None):
    """Truncates a string at a good length.

    Finds the rightmost space in a string, and truncates there. Lacking such
    a space, truncates at length.

    If an ellipsis is provided, the right most space is used that allows the
    addition of the ellipsis without being longer than length.
    """
    if ellipsis:
        ellipsis_length = len(ellipsis)
    else:
        ellipsis_length = 0

    if len(s) <= length:
        # Do not ellipsize if the item is not truncated.
        return s
    else:
        # find the rightmost space using a zero-indexed (+1) length minus the
        # length of the ellipsis.
        rightmost_space_index = length - ellipsis_length + 1
        end = s.rfind(' ', 0, rightmost_space_index)
        if end == -1:
            # no spaces found, just use max position
            end = length - ellipsis_length
        s = s[0:end]
        if ellipsis:
            s = '%s%s' % (s, ellipsis)
        return s

