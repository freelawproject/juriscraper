import re

PAGINATION_RE = re.compile(r"\b(?:Page|Pg)\s+\d+\s+of\s+\d+\b", re.I)
PAGINATION_COLON_RE = re.compile(r"\bPage:\s*\d+\b", re.I)
PAGINATION_PAGE_ID_RE = re.compile(r"\bPageID\s+#:\s*\d+\b", re.I)


def is_page_line(line: str) -> bool:
    """Detect if a line is a page-number marker.

    :param line: A single textual line extracted from a PDF.
    :return: True if the line matches "Page X of Y" or "Page: X"; False otherwise.
    """
    return bool(
        PAGINATION_RE.search(line)
        or PAGINATION_COLON_RE.search(line)
        or PAGINATION_PAGE_ID_RE.search(line)
    )


def is_doc_common_header(line: str) -> bool:
    """Identify common header/footer lines that should be ignored.

    :param line: A line extracted from a PDF.
    :return: True if the line is empty, begins with common header starters, or
    matches pagination, filing, date/time, or "Received" patterns. False otherwise.
    """
    bad_starters = (
        "Appellate",
        "Appeal",
        "Case",
        "Desc",
        "Document",
        "Entered",
        "Main Document",
        "Page",
        "Received:",
        "USCA",
    )
    doc_filed_re = re.compile(r"\b(Filed|Date Filed)\b")
    date_re = re.compile(r"\b\d{2}/\d{2}/\d{2}\b")
    time_re = re.compile(r"\b\d{2}:\d{2}:\d{2}\b")
    received_re = re.compile(r"\bReceived:\s*\d{2}/\d{2}/\d{2}(?:\d{2})?\b")

    if not line:
        return True
    if line.startswith(bad_starters):
        return True
    return bool(
        PAGINATION_RE.search(line)
        or PAGINATION_COLON_RE.search(line)
        or doc_filed_re.search(line)
        or date_re.search(line)
        or time_re.search(line)
        or received_re.search(line)
    )


def needs_ocr(content):
    """Determines if OCR is needed for a PDF.

    Every document in PACER (pretty much) has the case number written on the
    top of every page. This is a great practice, but it means that to test if
    OCR is needed, we need to remove this text and see if anything is left.

    As a fallback it removes these common headers so that if no text remains,
    we can be sure that the PDF needs OCR.

    :param content: The content of a PDF.
    :return: boolean indicating if OCR is needed.
    """
    lines = (ln.strip() for ln in content.splitlines())
    in_page = False
    other_content_count = 0
    saw_any_page = False
    for line in lines:
        if is_page_line(line):
            if in_page and other_content_count < 5:
                return True
            in_page = True
            saw_any_page = True
            other_content_count = 0
            continue

        if not in_page:
            continue

        # inside a page, count only non-common header lines
        if not is_doc_common_header(line):
            other_content_count += 1

    # end of document, close the trailing page
    if in_page and other_content_count < 5:
        return True

    # If no pages were found, fall back to the regular behavior of checking whether
    # any content remains after removing common headers.
    if not saw_any_page:
        for line in content.splitlines():
            if not is_doc_common_header(line.strip()):
                return False
        return True

    return False
