import re

from ..lib.string_utils import titlecase


def normalize_party_types(t):
    """Normalize various party types to as few as possible."""
    t = t.lower().strip()

    # Numerical types
    t = re.sub(r"defendant\s+\(\d+\)", r"defendant", t)
    t = re.sub(r"debtor\s+\d+", "debtor", t)

    # Assorted other
    t = re.sub(r"(thirdparty|3rd pty|3rd party)", r"third party", t)
    t = re.sub(r"(fourthparty|4th pty|4th party)", r"fourth party", t)
    t = re.sub(r"counter-(defendant|claimaint)", r"counter \1", t)
    t = re.sub(r"\bus\b", "u.s.", t)
    t = re.sub(r"u\. s\.", "u.s.", t)
    t = re.sub(r"united states", "u.s.", t)
    t = re.sub(r"jointadmin", "jointly administered", t)
    t = re.sub(r"consolidated-debtor", "consolidated debtor", t)
    t = re.sub(r"plaintiff-? consolidated", "consolidated plaintiff", t)
    t = re.sub(r"defendant-? consolidated", "consolidated defendant", t)
    t = re.sub(r"intervenor-plaintiff", "intervenor plaintiff", t)
    t = re.sub(r"intervenor pla\b", "intervenor plaintiff", t)
    t = re.sub(r"intervenor dft\b", "intervenor defendant", t)

    return titlecase(t)
