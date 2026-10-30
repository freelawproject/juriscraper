import re
from dataclasses import dataclass
from datetime import date, datetime

from lxml import html
from lxml.html import HtmlElement


@dataclass
class ContactAddress:
    title: str | None
    address_lines: list[str]
    city: str | None
    state: str | None
    zip_code: str | None
    email: str | None


EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
ID_RE = re.compile(r"(?:^|[^,]\s+)#\s*[A-Za-z0-9-]+\b")
ADDRESS_NUMBER = re.compile(
    r"\b(\d{1,6}(?:-\d{1,6})?(?:\s+\d+\/\d+)?[A-Za-z]?)\b"
)
ADDRESS_RE = r"([^,]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$"
DOCKET_NUMBER_RE = r"No\.\s*([^\s<]+)"

DATE_FORMATS = (
    "%B %d, %Y",  # July 3, 2024
    "%b %d %Y",  # Jul 03 2024
    "%b %d, %Y",  # Jul 03, 2024
    "%m/%d/%Y",  # 08/16/2024
)

LOWER_COURT_PATTERNS = {
    "common_prefix": re.compile(
        r"^\d+(?:-[A-Za-z]+)?-\d+(?:(?:[;/,-]-\d+)+|(?:,-\d+)*,-?|(?:/\d+)+)$"
    ),
    "comma_correct_prefix": re.compile(r"^(\d+-[A-Za-z]+, )*\d+-[A-Za-z]+$"),
    "special_formats": [
        re.compile(r"^(CR|CA)-\d+-\d+$"),
        re.compile(r"^\d+-\d+-\d+-[A-Za-z]+$"),
    ],
}

DOC_NUM_RE = r"DocketPDF/\d+/[^/]+/(\d+)/"


def clean_whitespace(text: str | None) -> str:
    """Collapse whitespace to single spaces.

    :param text: Raw text.
    :return: Normalized text to a single-line.
    """
    return "" if not text else re.sub(r"\s+", " ", text).strip()


def map_contacts_header_to_type(header_text: str) -> str | None:
    """Map table section headers to normalized types.

    :param header_text: Text to be mapped.
    :return: Normalized party type or None.
    """
    t = (header_text or "").strip().lower()
    if "petitioner" in t:
        return "Petitioner"
    if "respondent" in t:
        return "Respondent"
    if "other" in t:
        return "Other"
    return None


def parse_address_title(lines: list[str]) -> tuple[str | None, int]:
    """Extract the party title from address lines and determine where the address begins.

    :param lines: A list of text lines containing the party title and address.
    :return: A twp tuple where the first element is the concatenated title
    string and th index where the address starts.
    """
    title_parts = []
    start_add_idx = 0
    # Parse title.
    for j, ln in enumerate(lines):
        if ID_RE.match(ln):
            # Omit lines starting with # like #1098260
            continue
        if ADDRESS_NUMBER.search(ln):
            # Match the start of an address by looking for a street number.
            start_add_idx = j
            break
        title_parts.append(ln)

    title = ", ".join(title_parts) or None
    return title, start_add_idx


def parse_address_lines(
    lines: list[str], start_add_idx: int
) -> ContactAddress:
    """Parse the address components starting from a given index.

    :param lines: A list of text lines containing the address data.
    :param start_add_idx: Index indicating where the address lines begin.
    :return: A ContactAddress object.
    """

    address_lines: list[str] = (
        lines[start_add_idx:] if start_add_idx < len(lines) else []
    )

    # parse City/State/Zip
    city = state = zip_code = None
    if address_lines:
        last = address_lines[-1]
        if m := re.search(ADDRESS_RE, last):
            city, state, zip_code = (
                m.group(1).strip(),
                m.group(2),
                m.group(3),
            )
            address_lines = address_lines[:-1]

    return ContactAddress(
        title=None,
        address_lines=address_lines,
        city=city,
        state=state,
        zip_code=zip_code,
        email=None,
    )


def parse_description_html(td: HtmlElement) -> str:
    """Parse the cell content up to the first <br>, excluding
    .documentlinks.

    :param td: <td> element with the text description.
    :return: The description_html.
    """
    parts = []
    if td is None:
        return ""

    if td.text:
        parts.append(td.text)

    for child in td:
        tag = getattr(child, "tag", "")
        if tag and tag.lower() == "br":
            break
        # If a documentlinks span appears before a <br>, stop there too.
        if "documentlinks" in (child.get("class") or ""):
            break

        parts.append(html.tostring(child, encoding="unicode"))
        # Include its tail too.
        if child.tail:
            parts.append(child.tail)

    return "".join(parts)


def normalize_date(date_str: str | None) -> date | None:
    """Convert a date string to YYYY-MM-DD using common SCOTUS formats.

    :param date_str: Raw date string (e.g., "July 3, 2024", "Jul 03 2024", "08/16/2024")
    :return: A date python object or None
    """
    if not date_str:
        return None
    s = date_str.strip()
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(s, date_format).date()
        except ValueError:
            continue
    return None


def _apply_prefix(prefix: str, parts: list[str]) -> list[str]:
    """Prepend prefix to numeric parts."""
    return [
        f"{prefix}{p.strip()}" if p.strip().isdigit() else p.strip()
        for p in parts
    ]


def clean_lower_court_cases(raw_text: str) -> list[str]:
    """Clean and normalize lower court case numbers from various formats.

    :param raw_text: Raw text to be cleaned.
    :return: A list of lower court case numbers.
    """
    raw_text = raw_text.replace("(", "").replace(")", "").strip()

    # Case Slash-separated numbers with the same prefix: "98-35309/35509" or  "96-C-235/239/240/241"
    # Negative prefix-separated numbers: "99-1845,-1846,-1847,-197" or "98-60240,-60454,-60467,-"
    # "98-4033;-4214;-4246"
    if LOWER_COURT_PATTERNS["common_prefix"].match(raw_text):
        # slash case
        if "/" in raw_text and not re.search(r"[;,]", raw_text):
            parts = raw_text.split("/")
            prefix_match = re.match(r"(.*-)(\d+)$", parts[0])
            if not prefix_match:
                return raw_text.split(",")
            prefix = prefix_match.group(1)
            return _apply_prefix(prefix, [p.lstrip("-") for p in parts])

        # Mixed or negative-prefix (commas/semicolons and possibly slashes after the first number)
        # Supports optional letter segment, e.g. "96-C-235"
        prefix_match = re.match(r"(\d+(?:-[A-Za-z]+)?-)(\d+)", raw_text)
        if not prefix_match:
            return raw_text.split(",")

        prefix = prefix_match.group(1)
        suffix = prefix_match.group(2)
        numbers = [suffix] + re.split(
            r"[;,/]", raw_text[len(prefix_match.group(0)) :]
        )
        return [f"{prefix}{n.strip('-')}" for n in numbers if n.strip("-")]

    # Case Comma-separated items with prefixes already correct: "33094-CW, 33095-CW"
    if LOWER_COURT_PATTERNS["comma_correct_prefix"].match(raw_text):
        return raw_text.split(",")

    # Case Ampersand-separated with prefixes or 'See also'-separated with prefixes: "95-56639 & 96-55194" or "95-56639 See also 96-55194"
    if "See also" in raw_text:
        return raw_text.replace(" See also ", ",").split(",")

    # Case Preserve specific formats: "CR-99-1140", "1998-CA-0022039-MR"
    if any(p.match(raw_text) for p in LOWER_COURT_PATTERNS["special_formats"]):
        return raw_text.split(",")

    # Case Range expansion: "97-1715/98-1111 to 1115" or "97-1715/1111 to 1115"
    if re.search(r"\d+/\d+(-\d+)? to \d+", raw_text):
        parts = raw_text.split("/")
        cleaned = [parts[0]]
        range_part = parts[1]

        if " to " in range_part:
            start, end = range_part.split(" to ")
            if "-" in start:
                sprefix, snum = re.match(r"(\d+)-(\d+)", start).groups()
                cleaned.append(f"{sprefix}-{snum}")
                end_num = int(re.match(r"(\d+-)?(\d+)", end).groups()[-1])
                cleaned.extend(
                    f"{sprefix}-{i}" for i in range(int(snum) + 1, end_num + 1)
                )
            else:
                prefix = parts[0].split("-")[0]
                s, e = map(int, range_part.split(" to "))
                cleaned.extend(f"{prefix}-{i}" for i in range(s, e + 1))
        else:
            cleaned.append(f"{parts[0].split('-')[0]}-{range_part.strip()}")

        return cleaned

    # Default cleanup for other separators
    return [
        p.strip()
        for p in re.sub(r"[;&\n]", ",", raw_text).split(",")
        if p.strip()
    ]
