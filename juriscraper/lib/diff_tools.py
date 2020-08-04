import difflib
import string

import re

from .string_utils import harmonize

STOP_WORDS = (
    "a|an|and|as|at|but|by|en|etc|for|if|in|is|of|on|or|the|to|v\.?|via|"
    "vs\.?|et|al|appellants?|defendants?|administrator|"
    "plaintiffs?|error|others|against|ex|parte|complainants?|original|"
    "claimants?|devisee|executrix|executor|comm(issione)?\'?r"
)
STOP_WORDS_RE = re.compile(r"^(%s)$" % STOP_WORDS)


def normalize_phrase(phrase):
    """Clean up words or phrases before sending them to be compared.

     - Harmonize things like United States, USA, etc.
     - Normalize to lower case.
     - Remove punctuation.
     - Remove stop words.
    """
    phrase = harmonize(phrase)
    phrase = phrase.lower()

    # strip punctuation
    exclude = set(string.punctuation)
    phrase = "".join(ch for ch in phrase if ch not in exclude)

    words = re.split("[\t ]", phrase)
    result = []
    for word in words:
        word = STOP_WORDS_RE.sub("", word)
        result.append(word)
    return "".join(result)


def get_closest_match_index(word, possibilities):
    """Find the string that is most similar to the target string. Uses difflib's
    SequenceMatcher under the covers.

    :param word: The string to match to.
    :param possibilities: A list of possible matches.
    :return: The index of the closest matching possibility, if any. Else, return
    None.
    """
    word = normalize_phrase(word)
    possibilities = [normalize_phrase(x) for x in possibilities]
    try:
        match = difflib.get_close_matches(
            word, possibilities, n=1, cutoff=0.1
        )[0]
    except IndexError:
        # No good matches.
        return None
    return possibilities.index(match)
