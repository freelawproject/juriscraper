import re
from dataclasses import dataclass

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
