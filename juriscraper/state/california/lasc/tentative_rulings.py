"""Parsers for the Los Angeles Superior Court tentative rulings site.

The court publishes the tentative rulings of civil courtrooms at
`TENTATIVE_RULINGS_URL`. The search page lists every courtroom that is
currently publishing, one option per location, department and hearing date,
and posting one of those options back returns a page holding each tentative
ruling that courtroom issued for that date.

Only current and upcoming hearing dates are listed: a ruling is taken down
once its hearing has passed, so a caller that wants to keep them has to
capture every listed option at least daily.
"""

import html
import re
from datetime import date

from lxml import html as lxml_html
from pydantic import BaseModel
from typing_extensions import override

from juriscraper.abstract_parser import LegacyParser
from juriscraper.lib.html_utils import hidden_input_fields
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.state.california.lasc.common import parse_date

logger = make_default_logger()

TENTATIVE_RULINGS_URL = (
    "https://www.lacourt.ca.gov/tentativeRulingNet/ui/main.aspx?casetype=civil"
)

# The ASP.NET control that lists the publishing courtrooms. Its `name` carries
# the page's control hierarchy, which the court has changed before, so it is
# looked up by the stable tail of its `id` rather than hardcoded.
DEPARTMENT_SELECT_XPATH = "//select[contains(@id, 'List2DeptDate')]"

# Each ruling opens with this header. The rest of the page is HTML pasted in
# from word processors and too malformed to walk as a tree, so rulings are
# located in the raw text instead. The case number is whatever the clerk
# typed, which includes the numbers of cases transferred in from other
# counties (e.g. 30-2026-01564595) and the occasional typo.
RULING_HEADER_RE = re.compile(
    r"<B>\s*Case\s+Number:\s*</B>\s*(?P<case_number>[^\s&<]+)"
    r"(?:\s|&nbsp;)*<B>\s*Hearing\s+Date:\s*</B>\s*"
    r"(?P<hearing_date>[A-Za-z]+\s+\d{1,2},\s+\d{4})"
    r"(?:\s|&nbsp;)*<B>\s*Dept:\s*</B>\s*(?P<department>[^<]+?)\s*<P>",
    re.IGNORECASE,
)
# The site closes every ruling with an empty `wp` span before the rule that
# separates it from the next one, including the last ruling on the page. The
# site's rule is a bare `<HR>`: the rules word processors put inside rulings,
# such as the one above a ruling's footnotes, carry attributes and must not
# end the ruling.
RULING_END_RE = re.compile(r'<span\s+name="wp"|<hr\s*/?>', re.IGNORECASE)
# Courtrooms print the case name as an underlined span ahead of the ruling.
# Requiring the underline keeps a ruling that happens to open with a plain
# span from losing its first paragraph to the case name. Some courtrooms
# underline the calendar number and the name as two spans, the second nested
# in plain wrapper spans that also hold the ruling, so the wrappers are
# captured to be kept with the ruling.
CASE_NAME_RE = re.compile(
    r"^\s*(?P<wrappers>(?:<span\b(?![^>]*underline)[^>]*>\s*)*)"
    r"<span\b[^>]*underline[^>]*>(?P<case_name>.*?)</span>",
    re.IGNORECASE | re.DOTALL,
)
CALENDAR_NUMBER_RE = re.compile(r"^#\s*(?P<number>\w+)\s*-\s*(?P<rest>.*)$")
# A Los Angeles case number and the label courtrooms type in front of one.
# Both are spelled once here and composed into the patterns below, so that a
# court that starts writing them differently is one edit rather than five.
LASC_CASE_NUMBER = r"\d{2}[A-Z]{4}\d{5}|[A-Z]{2}\d{6}"
LASC_CASE_NUMBER_RE = re.compile(rf"^(?:{LASC_CASE_NUMBER})$")
CASE_NUMBER_LABEL = r"Case\s*(?:No\.?|Number|#)"
LEADING_CASE_NUMBER_RE = re.compile(rf"^(?:{LASC_CASE_NUMBER})\s*[:\-–—]?\s+")
LEADING_BREAKS_RE = re.compile(r"^(?:\s|<br\b[^>]*>)+", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
COURTHOUSE_RE = re.compile(r"^\((?P<courthouse>.+?):\s+Dept\.")

# Most courtrooms don't underline the case name but type it into the ruling
# itself, each in its own layout. The patterns below read the common layouts
# from the ruling's opening lines.
NON_TEXT_RE = re.compile(
    r"<!--.*?-->|<(?P<tag>style|script)\b.*?</(?P=tag)\s*>",
    re.IGNORECASE | re.DOTALL,
)
LINE_BREAK_RE = re.compile(
    r"<br\b[^>]*>|</?(?:p|div|li|td|th|tr|table|h[1-6])\b[^>]*>",
    re.IGNORECASE,
)
HEADING_LINES = 25
LABELED_CASE_NUMBER_RE = re.compile(
    rf"\b{CASE_NUMBER_LABEL}\s*:?\s*#?\s*"
    rf"(?P<number>{LASC_CASE_NUMBER})\b",
    re.IGNORECASE,
)
# "CASE NAME: Chavez v. City of Rosemead", or the label alone on its line
# with the name on the next, which matches with an empty name.
NAME_LABEL_RE = re.compile(
    r"^(?:Case\s*Name\s*(?::|$)|(?:Case|Caption)\s*:)\s*(?P<name>.*)$",
    re.IGNORECASE,
)
LABEL_RE = re.compile(r"^[A-Za-z][A-Za-z .#/]{1,30}:")
# Labels that some courtrooms type after the name on the same line.
TRAILING_LABEL_RE = re.compile(
    rf"\s+(?:(?:COMPL?|PET)\.?\s+FILED|{CASE_NUMBER_LABEL}|TRIAL\s+DATE"
    r"|HEARING\s+DATE|DEPT\.?|JUDGE|MOVING\s+PART(?:Y|IES)"
    r"|RESPONDING\s+PART(?:Y|IES))\s*:.*$",
    re.IGNORECASE,
)
TRAILING_CASE_NUMBER_LABEL_RE = re.compile(
    rf"[\s,;]*{CASE_NUMBER_LABEL}\s*:?$", re.IGNORECASE
)
# What a case name is never: a case number, or a line with no letters in it.
NOT_A_NAME_RE = re.compile(rf"(?:{LASC_CASE_NUMBER})|[\d\W]+")
# A lone capital "V" is left out of the case-sensitive patterns below: it is
# far more often a middle initial. `MATTER_SENTENCE_RE` folds case, so it
# admits one.
VERSUS = r"\s(?:vs?\.?|V\.|VS\.?|Vs\.?)\s"
# "#4 - HERNANDEZ vs GM LLC", "25STCV15519 Jae Ho Son v. Cenocore, Inc." or
# "LAKE HUGHES RECOVERY v. COUNTY OF LOS ANGELES [25STCV05368]".
VERSUS_LINE_RE = re.compile(
    r"^(?:(?:No\.|#)\s*(?P<calendar_number>\d+)\s*[-–—:.]?\s*)?"
    rf"(?:(?:{LASC_CASE_NUMBER})\s*[:\-–—]?\s*)?"
    rf"(?P<name>\S.{{0,200}}?{VERSUS}.{{1,200}}?)"
    rf"(?:[\s,]*[\[(]?\s*(?:{CASE_NUMBER_LABEL}\s*:?\s*)?"
    rf"(?:{LASC_CASE_NUMBER})\s*[\])]?)?[\s,.;]*$"
)
# Lines that cite other cases, which name parties the same way.
CITATION_RE = re.compile(
    r"\(\s*\d{4}\s*\)|\d\s+(?:Cal\.|U\.S\.|F\.|S\.\s?Ct\.)|\b(?:supra|id\.)",
    re.IGNORECASE,
)
# "The Court tenders the following tentative decision in the matter X v. Y,
# Los Angeles County Superior Court case number 26STCV15490".
MATTER_SENTENCE_RE = re.compile(
    rf"\bin the matter (?:of )?(?P<name>.{{3,200}}?{VERSUS}.{{1,200}}?),\s*"
    r"(?:Los Angeles (?:County )?Superior Court )?case\s+(?:number|no\.?)",
    re.IGNORECASE,
)
# A pleading caption: the plaintiff, a line holding only "vs.", then the
# defendant, each side optionally followed by role and case number lines.
# Some courtrooms squeeze a bracketed note such as "[Tentative] Granted"
# into the caption.
VERSUS_ALONE_RE = re.compile(r"^(?:v|vs|versus)\.?$", re.IGNORECASE)
BRACKETED_NOTE_RE = re.compile(r"^\[[^\]]*\]")
CAPTION_NOISE_RE = re.compile(
    r"^(?:[\W_]+"
    r"|(?:Plaintiffs?|Petitioners?|Defendants?|Respondents?"
    r"|Cross-(?:Complainants?|Defendants?))\b.{0,40}"
    rf"|{CASE_NUMBER_LABEL}.*|{LASC_CASE_NUMBER}"
    r"|(?:Hearing|Trial)\s+(?:Date|Time).*|Dept\..*|Department\b.*)$",
    re.IGNORECASE,
)
COURT_HEADING_RE = re.compile(
    r"TENTATIVE|SUPERIOR\s+COURT|COUNTY\s+OF|DISTRICT|COURTHOUSE",
    re.IGNORECASE,
)
# The tail of a caption's party list: further parties after a semicolon, and
# the Doe defendants.
PARTY_TAIL_RE = re.compile(
    r"\s*(?:;.*|,?\s*(?:and\s+)?DOES\s+\d.*)$", re.IGNORECASE
)
INDIVIDUAL_RE = re.compile(r",\s*an?\s+individual\b\.?", re.IGNORECASE)
ET_AL_RE = re.compile(r"\bet\.?\s+al\b", re.IGNORECASE)


class TentativeRulingOption(BaseModel):
    """A courtroom and hearing date the search page lists rulings for.

    :ivar value: The option's value, to post back to fetch its rulings.
    :ivar location_code: The court's code for the courthouse, e.g. ``ALH``.
    :ivar courthouse: The courthouse name as the option labels it.
    :ivar department: The department, e.g. ``X`` or ``309``.
    :ivar hearing_date: The hearing date the rulings are for.
    """

    value: str
    location_code: str
    courthouse: str
    department: str
    hearing_date: date


class TentativeRuling(BaseModel):
    """One tentative ruling as the court published it.

    :ivar case_number: The case number, e.g. ``24NNCV01819``. Normally as
        printed in the ruling's header; when that isn't a well-formed Los
        Angeles case number and the ruling itself labels one, the labeled
        number is used instead.
    :ivar hearing_date: The date of the hearing the ruling is for.
    :ivar department: The department that issued the ruling.
    :ivar calendar_number: The matter's position on the day's calendar, when
        the courtroom numbers its matters.
    :ivar case_name: The case name, as close to how the courtroom gave it as
        the layout allows. A courtroom that marks the name up as a name, or
        labels it, is quoted; one that only prints a pleading caption has a
        name built from it, shortened to the first party on each side. This
        is a best effort, empty when no name was found.
    :ivar ruling_html: The ruling as the courtroom published it. This is
        unsanitized third-party HTML and must be cleaned before display.
    """

    case_number: str
    hearing_date: date
    department: str
    calendar_number: str | None
    case_name: str
    ruling_html: str


def _clean_text(value: str) -> str:
    """Strip tags and entities and collapse whitespace.

    :param value: An HTML fragment.
    :return: Its text on a single line.
    """
    text = html.unescape(TAG_RE.sub(" ", value))
    return " ".join(text.split())


def _text_lines(fragment: str) -> list[str]:
    """Split an HTML fragment into its lines of text.

    Word processors wrap their HTML source at arbitrary points, so only line
    breaks and block elements start a new line.

    :param fragment: An HTML fragment.
    :return: The non-blank lines, whitespace collapsed.
    """
    text = " ".join(NON_TEXT_RE.sub("", fragment).split())
    text = html.unescape(TAG_RE.sub("", LINE_BREAK_RE.sub("\n", text)))
    lines = (" ".join(line.split()) for line in text.split("\n"))
    return [line for line in lines if line]


def _tidy_name(name: str) -> str:
    """Remove the punctuation and labels a name was typed next to.

    :param name: A case name as found in a ruling.
    :return: The name alone.
    """
    name = TRAILING_CASE_NUMBER_LABEL_RE.sub("", name.strip())
    return re.sub(r"[\s,;:¿]+$", "", name)


def _labeled_name(lines: list[str]) -> str:
    """Find a case name typed after a label such as ``CASE NAME:``.

    :param lines: The ruling's lines of text.
    :return: The name, or an empty string.
    """
    for index, line in enumerate(lines[:HEADING_LINES]):
        if not (label := NAME_LABEL_RE.match(line)):
            continue
        name = label.group("name")
        if not name and index + 1 < len(lines):
            if LABEL_RE.match(lines[index + 1]):
                continue
            name = lines[index + 1]
        name = _tidy_name(TRAILING_LABEL_RE.sub("", name))
        # "Case: 24STCV01234" labels a number, not a name.
        if name and not NOT_A_NAME_RE.fullmatch(name):
            return name
    return ""


def _caption_party(party: str) -> str:
    """Shorten one side of a pleading caption to its first party.

    :param party: The side as captioned, e.g. ``ALLA KUTZ, an individual;
        IGOR KUTZ, an individual and DOES 1 through 20, inclusive``.
    :return: The first party, marked ``et al.`` when others were dropped.
    """
    party = INDIVIDUAL_RE.sub("", party)
    first = _tidy_name(PARTY_TAIL_RE.sub("", party))
    if first != _tidy_name(party) and not ET_AL_RE.search(first):
        first = f"{first}, et al."
    return first


def _caption_name(lines: list[str]) -> str:
    """Find the case name in a pleading caption.

    :param lines: The ruling's lines of text.
    :return: ``plaintiff v. defendant``, or an empty string.
    """
    for index, line in enumerate(lines[:HEADING_LINES]):
        if not VERSUS_ALONE_RE.match(line):
            continue
        plaintiff = next(
            (
                above
                for above in reversed(lines[:index])
                if not CAPTION_NOISE_RE.match(above)
                and not BRACKETED_NOTE_RE.match(above)
            ),
            "",
        )
        if not plaintiff or COURT_HEADING_RE.search(plaintiff):
            continue
        # The defendant can wrap onto a few lines. Only a caption that ends
        # in a role or case number line is trusted, so body text following a
        # stray "vs." isn't taken for a party.
        defendant: list[str] = []
        for below in lines[index + 1 : index + 6]:
            if BRACKETED_NOTE_RE.match(below):
                continue
            if CAPTION_NOISE_RE.match(below):
                break
            defendant.append(below)
        else:
            continue
        if defendant:
            return (
                f"{_caption_party(plaintiff)} v. "
                f"{_caption_party(' '.join(defendant))}"
            )
    return ""


def _versus_line_name(lines: list[str]) -> tuple[str, str | None]:
    """Find a case name typed as a line of its own near the ruling's top.

    :param lines: The ruling's lines of text.
    :return: The name, or an empty string, and the calendar number if the
        line carried one.
    """
    for line in lines[:10]:
        if len(line) > 250 or CITATION_RE.search(line):
            continue
        if versus := VERSUS_LINE_RE.match(line):
            return (
                _tidy_name(versus.group("name")),
                versus.group("calendar_number"),
            )
    return "", None


def _typed_case_name(ruling_html: str) -> tuple[str, str | None]:
    """Find the case name a courtroom typed into a ruling.

    :param ruling_html: The ruling.
    :return: The name, or an empty string, and the calendar number if one
        was typed beside the name.
    """
    lines = _text_lines(ruling_html)
    if name := _labeled_name(lines) or _caption_name(lines):
        return name, None
    if matter := MATTER_SENTENCE_RE.search(" ".join(lines[:5])):
        return _tidy_name(matter.group("name")), None
    return _versus_line_name(lines)


def _case_number(header_number: str, ruling_html: str) -> str:
    """Choose the case number of a ruling.

    :param header_number: The number printed in the ruling's header.
    :param ruling_html: The ruling.
    :return: The header's number, unless it isn't a well-formed Los Angeles
        case number and the ruling's opening lines label one.
    """
    number = header_number.upper()
    if LASC_CASE_NUMBER_RE.match(number):
        return number
    heading = " ".join(_text_lines(ruling_html)[:HEADING_LINES])
    if labeled := LABELED_CASE_NUMBER_RE.search(heading):
        return labeled.group("number").upper()
    return number


def build_department_form_data(
    search_page_html: str, option_value: str
) -> dict[str, str]:
    """Build the form data that fetches one courtroom's rulings.

    The search page is an ASP.NET WebForms page, so the post has to echo back
    the page's hidden state fields (``__VIEWSTATE`` and its companions).

    :param search_page_html: The search page, fetched in the same session the
        form data will be posted from.
    :param option_value: The `TentativeRulingOption.value` to fetch.
    :return: The form fields to post to `TENTATIVE_RULINGS_URL`.
    :raises ValueError: If the page has no courtroom list.
    """
    tree = lxml_html.fromstring(search_page_html)
    selects = tree.xpath(DEPARTMENT_SELECT_XPATH)
    if not selects:
        raise ValueError("The search page has no courtroom list.")
    # This site needs only ASP.NET's own state, which is the hidden fields
    # named with a leading double underscore.
    data = hidden_input_fields(tree, prefix="__")
    data[selects[0].get("name")] = option_value
    return data


class TentativeRulingOptionsParser(LegacyParser[list[TentativeRulingOption]]):
    """Parse the courtrooms the search page lists rulings for."""

    @override
    def _parse(self, i: str) -> list[TentativeRulingOption]:
        """Parse the search page's courtroom list.

        :param i: The search page.
        :return: One option per listed courtroom and hearing date. Options
            whose value can't be read are skipped and logged.
        """
        tree = lxml_html.fromstring(i)
        options: list[TentativeRulingOption] = []
        for option in tree.xpath(f"{DEPARTMENT_SELECT_XPATH}/option"):
            value = option.get("value", "")
            if not value:
                continue
            parts = [part.strip() for part in value.split(",")]
            label = " ".join(option.text_content().split())
            courthouse = COURTHOUSE_RE.match(label)
            try:
                location_code, department, hearing_date = parts
                parsed_date = parse_date(hearing_date)
            except ValueError:
                logger.warning(
                    "Skipping unreadable tentative ruling option %r", value
                )
                continue
            options.append(
                TentativeRulingOption(
                    value=value,
                    location_code=location_code,
                    courthouse=courthouse.group("courthouse")
                    if courthouse
                    else "",
                    department=department,
                    hearing_date=parsed_date,
                )
            )
        return options


class TentativeRulingsParser(LegacyParser[list[TentativeRuling]]):
    """Parse the rulings on one courtroom's tentative rulings page."""

    @override
    def _parse(self, i: str) -> list[TentativeRuling]:
        """Split the page into rulings.

        The department's own notice to litigants precedes the first ruling
        and is discarded.

        :param i: A courtroom's tentative rulings page.
        :return: The page's rulings in the order they were published. A page
            with no rulings yields an empty list.
        """
        headers = list(RULING_HEADER_RE.finditer(i))
        rulings: list[TentativeRuling] = []
        for index, header in enumerate(headers):
            next_start = (
                headers[index + 1].start()
                if index + 1 < len(headers)
                else len(i)
            )
            body = i[header.end() : next_start]
            if end := RULING_END_RE.search(body):
                body = body[: end.start()]

            case_name, calendar_number = "", None
            while not case_name and (name_match := CASE_NAME_RE.match(body)):
                case_name = _clean_text(name_match.group("case_name"))
                body = name_match.group("wrappers") + body[name_match.end() :]
                if numbered := CALENDAR_NUMBER_RE.match(case_name):
                    calendar_number = numbered.group("number")
                    case_name = numbered.group("rest").strip()
                case_name = LEADING_CASE_NUMBER_RE.sub("", case_name)
                if calendar_number is None:
                    # Only a bare calendar number sends the loop on to the
                    # next underlined span for the name.
                    break
            if not case_name:
                case_name, typed_calendar_number = _typed_case_name(body)
                calendar_number = calendar_number or typed_calendar_number

            hearing_date = header.group("hearing_date")
            rulings.append(
                TentativeRuling(
                    case_number=_case_number(
                        header.group("case_number"), body
                    ),
                    hearing_date=parse_date(hearing_date),
                    department=_clean_text(header.group("department")),
                    calendar_number=calendar_number,
                    case_name=case_name,
                    ruling_html=LEADING_BREAKS_RE.sub("", body).strip(),
                )
            )
        return rulings

    @override
    def validate(self, _output: list[TentativeRuling]) -> bool:
        """Reject output with a ruling that has no text.

        A ruling with an empty body means the page's markup no longer
        matches what this parser expects.

        :param _output: The parsed rulings.
        :return: Whether every ruling has text.
        """
        return all(_clean_text(r.ruling_html) for r in _output)
