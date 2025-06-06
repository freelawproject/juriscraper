import calendar
import re
import string
from datetime import timedelta

import geonamescache
from dateutil import parser

# For use in titlecase
BIG = (
    "3D|AFL|AKA|A/K/A|BMG|CBS|CDC|CDT|CEO|CIO|CNMI|D/B/A|DOJ|DVA|EFF|"
    "FCC|FTC|HSBC|IBM|II|III|IV|JJ|LLC|LLP|MCI|MJL|MSPB|ND|NLRB|PTO|"
    "SD|UPS|RSS|SEC|UMG|US|USA|USC|USPS|WTO"
)
SMALL = r"a|an|and|as|at|but|by|en|for|if|in|is|of|on|or|the|to|v\.?|via|vs\.?"
NUMS = "0123456789"
PUNCT = r"""!"#$¢%&'‘()*+,\-./:;?@[\\\]_—`{|}~"""
WEIRD_CHARS = r"¼½¾§ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜßàáâãäåæçèéêëìíîïñòóôœõöøùúûüÿ"
BIG_WORDS = re.compile(rf"^({BIG})[{PUNCT}]?$", re.I | re.U)
SMALL_WORDS = re.compile(r"^(%s)$" % SMALL, re.I)
SMALL_WORD_INLINE = re.compile(r"(^|\s)(%s)(\s|$)" % SMALL, re.I | re.U)
INLINE_PERIOD = re.compile(r"[a-z][.][a-z]", re.I)
INLINE_SLASH = re.compile(r"[a-z][/][a-z]", re.I)
INLINE_AMPERSAND = re.compile(r"([a-z][&][a-z])(.*)", re.I)
UC_ELSEWHERE = re.compile(r"[%s]*?[a-zA-Z]+[A-Z]+?" % PUNCT, re.U)
CAPFIRST = re.compile(r"^[%s]*?([A-Za-z])" % PUNCT)
SMALL_FIRST = re.compile(rf"^([{PUNCT}]*)({SMALL})\b", re.I | re.U)
SMALL_LAST = re.compile(rf"\b({SMALL})[{PUNCT}]?$", re.I | re.U)
SUBPHRASE = re.compile(r"([:;?!][ ])(%s)" % SMALL)
APOS_SECOND = re.compile(r"^[dol]{1}['‘]{1}[a-z]+$", re.I)
ALL_CAPS = re.compile(rf"^[A-Z\s{PUNCT}{WEIRD_CHARS}{NUMS}]+$")
UC_INITIALS = re.compile(r"^(?:[A-Z]{1}\.{1}|[A-Z]{1}\.{1}[A-Z]{1})+,?$")
MAC_MC = re.compile(r"^([Mm]a?c)(\w+.*)")


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
    text_sans_small_words = re.sub(SMALL_WORD_INLINE, "", text)
    if text_sans_small_words.isupper():
        # if, after removing small words, the entire string is uppercase,
        # we lowercase it
        if DEBUG:
            print("Entire string is uppercase, thus lowercasing.")
        text = text.lower()
    elif not text_sans_small_words.isupper() and DEBUG:
        print(f"Entire string not upper case. Not lowercasing: {text}")

    lines = re.split(r"[\r\n]+", text)
    processed = []
    for line in lines:
        all_caps = ALL_CAPS.match(line)
        words = re.split(r"[\t ]", line)
        tc_line = []
        for word in words:
            if DEBUG:
                print(f"Word: {word}")
            if all_caps:
                if UC_INITIALS.match(word):
                    if DEBUG:
                        print(f"  UC_INITIALS match for: {word}")
                    tc_line.append(word)
                    continue
                else:
                    if DEBUG:
                        print(f"  Not initials. Lowercasing: {word}")
                    word = word.lower()

            if APOS_SECOND.match(word):
                # O'Reiley, L'Oreal, D'Angelo
                if DEBUG:
                    print(f"  APOS_SECOND matched. Fixing it: {word}")
                word = word[0:3].upper() + word[3:]
                tc_line.append(word)
                continue

            if INLINE_PERIOD.search(word):
                if DEBUG:
                    print(
                        "  INLINE_PERIOD matched. Uppercasing if == 1 char: "
                        + word
                    )
                parts = word.split(".")
                new_parts = []
                for part in parts:
                    if len(part) == 1:
                        # It's an initial like U.S.
                        new_parts.append(part.upper())
                    else:
                        # It's something like '.com'
                        new_parts.append(part)
                word = ".".join(new_parts)
                tc_line.append(word)
                continue

            if INLINE_SLASH.search(word):
                # This repeats INLINE_PERIOD. Could be more elegant.
                if DEBUG:
                    print(
                        "  INLINE_SLASH matched. Uppercasing if == 1 char: "
                        + word
                    )
                parts = word.split("/")
                new_parts = []
                for part in parts:
                    if len(part) == 1:
                        # It's an initial like A/M
                        new_parts.append(part.upper())
                    else:
                        # It's something like 'True/False'
                        new_parts.append(part)
                word = "/".join(new_parts)
                tc_line.append(word)
                continue

            amp_match = INLINE_AMPERSAND.match(word)
            if amp_match:
                if DEBUG:
                    print(f"  INLINE_AMPERSAND matched. Uppercasing: {word}")
                tc_line.append(
                    f"{amp_match.group(1).upper()}{amp_match.group(2)}"
                )
                continue

            if UC_ELSEWHERE.match(word):
                if DEBUG:
                    print(f"  UC_ELSEWHERE matched. Leaving unchanged: {word}")
                tc_line.append(word)
                continue

            if SMALL_WORDS.match(word):
                if DEBUG:
                    print(f"  SMALL_WORDS matched. Lowercasing: {word}")
                tc_line.append(word.lower())
                continue

            if BIG_WORDS.match(word):
                if DEBUG:
                    print(f"  BIG_WORDS matched. Uppercasing: {word}")
                tc_line.append(word.upper())
                continue

            match = MAC_MC.match(word)
            if match and (word not in ["mack", "machine"]):
                if DEBUG:
                    print(f"  MAC_MAC matched. Capitalizing: {word}")
                tc_line.append(
                    "%s%s"
                    % (
                        match.group(1).capitalize(),
                        match.group(2).capitalize(),
                    )
                )
                continue

            hyphenated = []
            for item in word.split("-"):
                hyphenated.append(_uppercase_word(item))
            tc_line.append("-".join(hyphenated))

        result = " ".join(tc_line)

        result = SMALL_FIRST.sub(
            lambda m: f"{m.group(1)}{m.group(2).capitalize()}",
            result,
        )

        result = SMALL_LAST.sub(lambda m: m.group(0).capitalize(), result)
        result = SUBPHRASE.sub(
            lambda m: f"{m.group(1)}{m.group(2).capitalize()}",
            result,
        )

        processed.append(result)
        text = "\n".join(processed)

    # replace V. with v.
    text = re.sub(re.compile(r"\WV\.\W"), " v. ", text)

    return text


def _uppercase_word(word):
    """
    Helper function for uppercasing a word if it doesn't begin with Unicode characters.

    This is needed due to differences between Python 2 and 3.
    :param word: unicode string to uppercase
    """
    # if six.PY2:
    #    if word[0] in (u'\u2019',):
    #        return CAPFIRST.sub(lambda m: m.group(0).upper(), word[1:])

    return CAPFIRST.sub(lambda m: m.group(0).upper(), word)


def fix_camel_case(s):
    """Sometimes courts provide nasty camel-cased content instead of real
    words. This code attempts to fix that."""
    if " " in s:
        s_out = s
    else:
        s_out = s[0]
        for i in range(1, len(s)):
            # Iterate over the letters, starting with the second one.
            if s[i - 1].isupper() and s[i].isupper():
                # A pattern like 'PAPublic' --> PA Public
                try:
                    next_letter_is_lower = (
                        s[i + 1].islower() and s[i + 1] != "v"
                    )
                except IndexError:
                    # End of string. Break.
                    s_out += s[i]
                    continue
                if next_letter_is_lower:
                    s_out += f" {s[i]}"
                else:
                    s_out += s[i]
            elif s[i - 1].islower() and s[i].isupper():
                # A pattern like 'McLaughlin'
                try:
                    mac_or_mc = (s[i - 2] == "a" and s[i - 3] == "M") or s[
                        i - 2
                    ] == "M"
                except KeyError:
                    s_out += f" {s[i]}"
                if s[i - 1] == "c" and mac_or_mc:
                    s_out += s[i]
                else:
                    s_out += f" {s[i]}"
            elif s[i].isupper() and s[i - 1].islower():
                # Uppercase letter preceded by a lowercase one. Add a space then the letter.
                s_out += f" {s[i]}"
            else:
                s_out += s[i]
        # Fix v.'s that don't have spaces. These come in two forms:
        # 1. So and sov.so and so
        s_out = " ".join(re.sub(r"v\.", " v. ", s_out).split())
        # 2. So and sov so and so --> So and so v. so and so
        if "v." not in s_out:
            s_out = " ".join(re.sub("([^ ])v ", r"\1 v. ", s_out).split())

        # Fix strings like Governorof, Stateof, Secretaryofthe
        if "of" in s_out:
            s_out = re.sub(r"([a-zA-Z])of( |(?:the))", r"\1 of\2", s_out)
        if "the" in s_out:
            s_out = re.sub(r"([a-zA-Z])the ", r"\1 the ", s_out)

        # Fix strings like Santomenno,etal v. John Hancock Life Ins
        if "etal" in s_out:
            s_out = re.sub(r",?etal( |\Z)", " ", s_out).strip()

        # Fix strings like Inre SCH Corp v. CFI Class
        if "Inre" in s_out:
            s_out = re.sub(r"^Inre ", "In Re ", s_out)

    return s_out


# For use in harmonize function
# More details: http://www.law.cornell.edu/citation/4-300.htm
US = r"USA|U\.S\.A\.|U\.S\.?|U\. S\.?|(The )?United States of America|The United States"
UNITED_STATES = re.compile(r"^(%s)(,|\.)?$" % US, re.I)
ET_AL = re.compile(r",?\set\.?\sal\.?", re.I)
BW = (
    "appell(ee|ant)s?|claimants?|complainants?|defendants?|defendants?(--?|/)appell(ee|ant)s?"
    + r"|devisee|executor|executrix|pet(\.|itioner)s?|petitioners?(--?|/)appell(ee|ant)s?"
    + "|petitioners?(--?|/)defendants?|plaintiffs?|plaintiffs?(--?|/)appell(ee|ant)s?|respond(e|a)nts?"
    + "|respond(e|a)nts?(--?|/)appell(ee|ant)s?|cross(--?|/)respondents?|crosss?(--?|/)petitioners?"
    + "|cross(--?|/)appell(ees|ant)s?|deceased"
)
BAD_WORDS = re.compile(r"^(%s)(,|\.)?$" % BW, re.I)


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
    if not isinstance(text, str):
        text = str(text)

    # replace vs. with v.
    text = re.sub(re.compile(r"\svs\.?\s", re.IGNORECASE), " v. ", text)

    # replace lower case v without a period with v.
    text = re.sub(r"\sv\.?\s", " v. ", text)

    # Remove the BAD_WORDS.
    text = text.split()
    cleaned_text = []
    for word in text:
        word = re.sub(BAD_WORDS, "", word)
        cleaned_text.append(word)
    text = " ".join(cleaned_text)

    # split on all ' v. ' and then deal with United States variations.
    harmonized_parts = []
    parties = text.split(" v. ")
    for party in parties:
        party = party.strip()
        if UNITED_STATES.match(party):
            harmonized_parts.append("United States")
        elif party.lower() == "the state":
            harmonized_parts.append("State")
        else:
            # needed here, because we can't put "US" as a case-insensitive
            # word into the UNITED_STATES regex.
            party = re.sub(re.compile(r"^US$"), "United States", party)
            # no match
            harmonized_parts.append(party)

    result = " v. ".join(harmonized_parts)

    # Remove the ET_AL words.
    result = re.sub(ET_AL, "", result)

    # Fix the No. and Nos.
    if result.startswith("No.") or result.startswith("Nos."):
        result = re.sub(r"^Nos?\.\s+", "", result)

    return clean_string(result)


def clean_string(s):
    """Clean up strings.

    Accomplishes the following:
     - replaces HTML encoded characters with ASCII versions.
     - removes -, ' ', #, *, ; and ',' from the end of lines
     - converts to unicode.
     - removes weird white space and replaces with spaces.
    """
    # if not already unicode, make it unicode, dropping invalid characters
    # if not isinstance(s, unicode):
    s = force_unicode(s, errors="ignore")

    # Get rid of HTML encoded chars
    s = (
        s.replace("&rsquo;", "'")
        .replace("&rdquo;", '"')
        .replace("&ldquo;", '"')
        .replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("%20", " ")
        .replace("&#160;", " ")
    )

    # smart quotes
    s = (
        s.replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
    )

    # Get rid of weird punctuation
    s = s.replace("*", "").replace("#", "")

    # Strip bad stuff from the end of lines. Python's strip fails here because
    # we don't know the order of the various punctuation items to be stripped.
    # We split on the v., and handle fixes at either end of plaintiff or
    # appellant.
    bad_punctuation = r"(-|–|_|/|;|,|\s)*"
    bad_endings = re.compile(r"%s$" % bad_punctuation)
    bad_beginnings = re.compile(r"^%s" % bad_punctuation)

    s = s.split(" v. ")
    cleaned_string = []
    for frag in s:
        frag = re.sub(bad_endings, "", frag)
        frag = re.sub(bad_beginnings, "", frag)
        cleaned_string.append(frag)
    s = " v. ".join(cleaned_string)

    # get rid of '\t\n\x0b\x0c\r ', and replace them with a single space.
    s = " ".join(s.split())

    # Convert non-breaking spaces to regular spaces
    s = s.replace("\u00a0", " ")

    return s


def force_unicode(s, encoding="utf-8", strings_only=False, errors="strict"):
    # Borrows heavily from django.utils.encoding.force_unicode.
    # This should be applied to *input* not *output*!
    # Handle the common case first, saves 30-40% in performance when s
    # is an instance of unicode. This function gets called often in that
    # setting.
    if isinstance(s, str):
        return s
    try:
        if not isinstance(s, str):
            if hasattr(s, "__unicode__"):
                s = str(s)
            else:
                try:
                    s = str(str(s), encoding, errors)
                except UnicodeEncodeError:
                    if not isinstance(s, Exception):
                        raise
                    # If we get to here, the caller has passed in an Exception
                    # subclass populated with non-ASCII data without special
                    # handling to display as a string. We need to handle this
                    # without raising a further exception. We do an
                    # approximation to what the Exception's standard str()
                    # output should be.
                    s = " ".join(
                        [
                            force_unicode(arg, encoding, strings_only, errors)
                            for arg in s
                        ]
                    )
        elif not isinstance(s, str):
            # Note: We use .decode() here, instead of unicode(s, encoding,
            # errors), so that if s is a SafeString, it ends up being a
            # SafeUnicode at the end.
            s = s.decode(encoding, errors)
    except UnicodeDecodeError:
        if not isinstance(s, Exception):
            raise
        else:
            # If we get to here, the caller has passed in an Exception
            # subclass populated with non-ASCII bytestring data without a
            # working unicode method. Try to handle this without raising a
            # further exception by individually forcing the exception args
            # to unicode.
            s = " ".join(
                [
                    force_unicode(arg, encoding, strings_only, errors)
                    for arg in s
                ]
            )
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
        end = s.rfind(" ", 0, rightmost_space_index)
        if end == -1:
            # no spaces found, just use max position
            end = length - ellipsis_length
        s = s[0:end]
        if ellipsis:
            s = f"{s}{ellipsis}"
        return s


def convert_date_string(date_string, fuzzy=False, datetime=False):
    """Sanitize date string and convert into standard date object

    :param date_string: A string to convert to a datetime object.
    :param fuzzy: whether fuzzy string matching should be used, as defined by
    dateutil.
    :param datetime: If True, return a datetime object. If false, cast to a
    date.
    :return: datetime or date object, depending on the datetime parameter.
    """
    date_string = date_string.replace("(", "")
    date_string = date_string.replace(")", "")

    # python3 and lxml make for odd strings that we need to clean
    date_string = clean_if_py3(date_string)

    date_string = date_string.strip()
    if date_string == "N/A":
        return None

    dt = parser.parse(date_string, fuzzy=fuzzy)
    if datetime:
        return dt
    else:
        return dt.date()


def split_date_range_string(date_range_string):
    """This function requires a string in 'January - March 2016' format"""
    date_range_string = normalize_dashes(date_range_string)
    parts = date_range_string.split()
    if "-" not in date_range_string or len(parts) != 4:
        raise Exception(f'Unrecognized date format: "{date_range_string}"')
    month1, month2, year = parts[0], parts[2], parts[3]
    months = {v: k for k, v in enumerate(calendar.month_name)}
    last_day = calendar.monthrange(int(year), months[month2])[1]
    start_date = convert_date_string(f"{month1} 1, {year}")
    end_date = convert_date_string("%s %d, %s" % (month2, last_day, year))
    delta = end_date - start_date
    dates_in_range = [start_date + timedelta(d) for d in range(delta.days + 1)]
    return dates_in_range[int(len(dates_in_range) / 2)]


def normalize_dashes(raw_string):
    """Replace various dash formats with normal dash"""
    dashes = [
        # copied from http://www.w3schools.com/charsets/ref_utf_punctuation.asp
        "–",  # en dash
        "—",  # em dash
        "‐",  # hyphen
        "‑",  # non-breaking hyphen
        "‒",  # figure dash
        "―",  # horizontal bar
    ]
    normal = "-"
    for dash in dashes:
        raw_string = raw_string.replace(dash, normal)
    return raw_string


class CaseNameTweaker:
    def __init__(self):
        self._bad_words = None
        super().__init__()

    @property
    def bad_words(self):
        """A list of words that shouldn't be in small case names according to
        Blue Book rules.

        Includes:

         - Acronyms
         - Common names
         - Attorneys General
         - Large cities
         - Counties
         - States
         - Punctuation and capitalization variations on the above

        Created lazily and then cached the first time the property is called.
        """
        if self._bad_words is not None:
            return self._bad_words

        acros = [
            "a.g.p.",
            "c.d.c.",
            "c.i.a.",
            "d.o.c.",
            "e.e.o.c.",
            "e.p.a.",
            "f.b.i.",
            "f.c.c.",
            "f.d.i.c.",
            "f.s.b.",
            "f.t.c.",
            "i.c.c.",
            "i.n.s.",
            "i.r.s.",
            "n.a.a.c.p.",
            "n.l.r.b.",
            "p.l.c.",
            "s.e.c.",
            "s.p.a.",
            "s.r.l.",
            "u.s.",
            "u.s.a.",
            "u.s.e.e.o.c.",
            "u.s.e.p.a.",
        ]
        acros_sans_dots = [acro.replace(".", "") for acro in acros]
        # corp_acros = ['L.L.C.', 'L.L.L.P.', 'L.L.P.', 'L.P.', 'P.A.', 'P.C.',
        #              'P.L.L.C.',c ]
        # corp_acros_sans_dots = [acro.replace('.', '') for acro in corp_acros]
        common_names = [
            "state",
            "people",
            "smith",
            "johnson",
            "commissioner",
            "commonwealth",
        ]

        ags = [
            "Akerman",
            "Ashcroft",
            "Barr",
            "Bates",
            "Bell",
            "Berrien",
            "Biddle",
            "Black",
            "Bonaparte",
            "Bork",
            "Bradford",
            "Breckinridge",
            "Brewster",
            "Brownell",
            "Butler",
            "Civiletti",
            "Clark",
            "Clement",
            "Clifford",
            "Crittenden",
            "Cummings",
            "Cushing",
            "Daugherty",
            "Devens",
            "Evarts",
            "Filip",
            "Garland",
            "Gerson",
            "Gilpin",
            "Gonzales",
            "Gregory",
            "Griggs",
            "Grundy",
            "Harmon",
            "Hoar",
            "Holder",
            "Jackson",
            "Johnson",
            "Katzenbach",
            "Keisler",
            "Kennedy",
            "Kleindienst",
            "Knox",
            "Lee",
            "Legaré",
            "Levi",
            "Lincoln",
            "Lynch",
            "MacVeagh",
            "Mason",
            "McGranery",
            "McGrath",
            "McKenna",
            "McReynolds",
            "Meese",
            "Miller",
            "Mitchell",
            "Moody",
            "Mukasey",
            "Murphy",
            "Nelson",
            "Olney",
            "Palmer",
            "Pierrepont",
            "Pinkney",
            "Randolph",
            "Reno",
            "Richardson",
            "Rodney",
            "Rogers",
            "Rush",
            "Sargent",
            "Saxbe",
            "Sessions",
            "Smith",
            "Speed",
            "Stanbery",
            "Stanton",
            "Stone",
            "Taft",
            "Taney",
            "Thornburgh",
            "Toucey",
            "Whitacker",
            "Wickersham",
            "Williams",
            "Wirt",
        ]
        # self.corp_acros = corp_acros + corp_acros_sans_dots
        bad_words = (
            acros
            + acros_sans_dots
            + common_names
            + ags
            + self.make_geographies_list()
        )

        # Add variations with punctuation
        punctuation_bad_words = []
        for word in bad_words:
            for punctuation in string.punctuation:
                if not word.endswith(punctuation):
                    punctuation_bad_words.append(f"{word}{punctuation}")
        bad_words = bad_words + punctuation_bad_words

        bad_words = [s.lower() for s in bad_words]

        self._bad_words = bad_words
        return bad_words

    @staticmethod
    def make_geographies_list():
        """Make a flat list of cities, counties and states that we can exclude
        from short names.
        """
        geonames = geonamescache.GeonamesCache()

        # Make a list of cities with big populations.
        cities = [
            v["name"]
            for v in geonames.get_cities().values()
            if (v["countrycode"] == "US" and v["population"] > 150000)
        ]
        counties = [v["name"] for v in geonames.get_us_counties()]
        states = [v["name"] for v in geonames.get_us_states().values()]
        return cities + counties + states

    def make_case_name_short(self, s):
        """Creates short case names where obvious ones can easily be made."""
        parts = [part.strip().split() for part in s.split(" v. ")]
        if len(parts) == 1:
            # No v. Likely an "In re" or "Matter of" case.
            if len(parts[0]) <= 3:
                # Good length for a shortened case name.
                return s
            else:
                # Too long; too weird. Punt.
                return ""

        elif len(parts) == 2:
            # X v. Y --> [['X'], ['Y']]
            # X Y Z v. A B --> [['X', 'Y', 'Z'], ['A', 'B']]
            if len(parts[0]) == 1:
                if parts[0][0].lower() not in self.bad_words:
                    # Simple case: Langley v. Google
                    return parts[0][0]
                elif (
                    len(parts[1]) == 1
                    # Plaintiff was a bad_word. Try the defendant.
                    # Dallas v. Lissner
                    and parts[1][0].lower() not in self.bad_words
                ):
                    return parts[1][0]
            elif (
                len(parts[0]) > 1
                # Plaintiff part is longer than a single word, focus on the
                # defendant.
                and len(parts[1]) == 1
                # If the defendant is a single word.
                and parts[1][0].lower() not in self.bad_words
            ):
                # That's not a bad word.
                return parts[1][0]

        # More than 1 instance of v. or otherwise no matches --> Give up.
        return ""


def clean_if_py3(s):
    """
    Cleans up text if using Python 3

    :param s: string to clean
    :return: string un-modified on Python 2.x, string with raw literals replaced
             with their string forms on Python 3.x
    """
    replacements = [(r"\n", "\n"), (r"\t", "\t"), (r"\r", "\r")]

    for raw, replacement in replacements:
        s = s.replace(raw, replacement)

    return s
