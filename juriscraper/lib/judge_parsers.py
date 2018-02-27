from .string_utils import titlecase

titles = [
    'judge', 'magistrate', 'district', 'chief', 'senior',
    'bankruptcy', 'mag.', 'magistrate-judge', 'mag/judge', 'mag',
    'visiting', 'special', 'senior-judge', 'master', 'u.s.magistrate',
]
blacklist = [
    'a998', 'agb', 'am', 'associated', 'ca', 'cases', 'cet', 'ch.', 'cla',
    'clerk', 'cp', 'cvb', 'db', 'debt-magistrate', 'discovery', 'dj', 'docket',
    'duty', 'duty', 'ec', 'eck', 'general', 'grc', 'gs', 'hhl', 'hon',
    'honorable', 'inactive', 'jne', 'jv', 'kec', 'law', 'lc', 'llh', 'lq',
    'maryland', 'mediator', 'merged', 'mj', 'mmh', 'msh', 'mwd', 'no', 'none',
    'prisoner', 'pslc', 'pro', 'pso', 'pt', 'rmh', 'se', 'sf', 'show',
    'successor', 'u.s.', 'tjc', 'unassigned', 'unassigned2', 'unassigneddj',
    'unknown', 'us', 'usdc', 'vjdistrict',
]

judge_normalizers = {
    # Generic Judge & Bankruptcy Judge we merge together for simplicity.
    '': 'jud',
    'Judge': 'jud',
    'Judge Judge': 'jud',
    'District Judge': 'jud',
    'Visiting Judge': 'jud',
    'Bankruptcy': 'jud',
    'Bankruptcy Judge': 'jud',

    # Chief (normalize to jud for now, due to low sample size)
    'Chief': 'jud',
    'Chief Judge': 'jud',
    'Chief District Judge': 'jud',

    # Magistrate
    'Mag': 'mag',
    'Mag Judge': 'mag',
    'mag/judge': 'mag',
    'Magistrate': 'mag',
    'Magistrate Judge': 'mag',
    'Magistrate-Judge': 'mag',
    'Magistrate Judge Mag': 'mag',
    'Magistrate Judge Magistrate': 'mag',
    'Magistrate Judge Magistrate Judge': 'mag',

    # Chief Magistrate (normalize to magistrate for now, due to low sample size)
    'Chief Magistrate': 'mag',
    'Chief Magistrate Judge': 'mag',

    # Senior
    'Senior Judge': 'ret-senior-jud',
    'Senior-Judge': 'ret-senior-jud',

    # Special Master
    'Special Master': 'spec-m',
    'Chief Special Master': 'c-spec-m',
}


def normalize_judge_titles(title):
    """Normalize judge titles

    Take in a string like "Magistrate Judge" and return the normalized
    abbreviation from the POSITION_TYPES variable. Assumes that input is
    titlecased.

    Also normalizes things like:
     - District Judge --> Judge
     - Blank --> Judge
     - Bankruptcy Judge --> Judge
    """
    return judge_normalizers.get(title, 'UNKNOWN: %s' % title)


def normalize_judge_names(name):
    """Cleans up little issues with people's names"""
    out = []
    words = name.split()
    for i, w in enumerate(words):
        # Michael J Lissner --> Michael J. Lissner
        if len(w) == 1 and w.isalpha():
            w = '%s.' % w

        # Michael Lissner Jr --> Michael Lissner Jr.
        if w.lower() in ['jr', 'sr']:
            w = '%s.' % w

        # J. Michael Lissner --> Michael Lissner
        # J. G. Lissner --> J. G. Lissner
        if i == 0 and w.lower() in ['j.', 'j']:
            next_word = words[i + 1]
            if not any([len(next_word) == 2 and next_word.endswith('.'),
                        len(next_word) == 1]):
                # Drop the word.
                continue
        out.append(w)

    return ' '.join(out)


def normalize_judge_string(judge):
    """Split a string representing a judge returning their name and title.

    This code was generated and tested against all judge strings in the RECAP
    Archive.

    :param judge: A string representing a judge, e.g.
    :return: A tuple of the judge's name and their normalized position.

    >>> normalize_judge_string('Honorable Sue W. Wright')
    ('Sue W. Wright', 'jud')
    """
    judge = judge.replace(',', '')
    words = judge.lower().split()

    # Nuke bad junk (punct., j, blacklist, etc.)
    title_words = []
    name_words = []
    for w in words:
        contains_parens = '(' in w or ')' in w
        starts_poorly = w.startswith('-') or w.startswith('~')
        blacklisted = w in blacklist
        long_abbrev = (len(w) > 2 and '.' in w and w not in ['jr.', 'sr.'])
        if any([contains_parens, starts_poorly, blacklisted, long_abbrev]):
            continue
        if w in titles:
            title_words.append(w)
        else:
            name_words.append(w)

    title = normalize_judge_titles(titlecase(' '.join(title_words)))
    name = normalize_judge_names(titlecase(' '.join(name_words)))

    return name, title
