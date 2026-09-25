"""What the Los Angeles Superior Court's three sites have in common.

Each site is its own application with its own markup, and the parsers are
kept apart accordingly. What they share is the court's way of writing things
down, which lives here so that all three read it the same way.
"""

from datetime import date, datetime

from juriscraper.lib.string_utils import convert_date_string


def parse_date(value: str) -> date:
    """Read a date the court printed.

    The three sites write dates differently — ``09/21/2026`` on the
    calendar, ``7/9/2025`` on a case summary, ``September 14, 2026`` atop a
    tentative ruling — so this reads what the court wrote rather than
    insisting on one layout.

    :param value: The date as the court printed it.
    :return: The date.
    :raises ValueError: If the value isn't a date, which is also what the
        court's empty cells come to.
    """
    parsed = convert_date_string(value)
    if isinstance(parsed, datetime):
        return parsed.date()
    if parsed is None:
        raise ValueError(f"{value!r} is not a date.")
    return parsed
