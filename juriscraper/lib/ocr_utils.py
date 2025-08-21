import re

from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger()

PAGINATION_RE = re.compile(r"\b(?:Page|Pg)\s+\d+\s+of\s+\d+\b", re.I)
PAGINATION_COLON_RE = re.compile(r"\bPage:\s*\d+\b", re.I)
PAGINATION_PAGE_ID_RE = re.compile(r"\bPageID\s+#:\s*\d+\b", re.I)
PAGINATION_NUMBER_DASH_RE = re.compile(r"- (\d+) -")


def is_page_line(line: str) -> bool:
    """Detect if a line is a page-number marker.

    :param line: A single textual line extracted from a PDF.
    :return: True if the line matches "Page X of Y" or "Page: X"; False otherwise.
    """
    return bool(
        PAGINATION_RE.search(line.strip())
        or PAGINATION_COLON_RE.search(line.strip())
        or PAGINATION_PAGE_ID_RE.search(line.strip())
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


def needs_ocr(content, page_count=0, line_count_threshold=5):
    """Determines if OCR is needed for a PDF (PACER-aware).

    Checks for valid content lines between pages using PACER-style headers.
    Falls back to missing-pages logic if no page lines are found.

    :param content: The content of a PDF.
    :param page_count: The expected number of pages in the PDF.
    :param line_count_threshold: Minimum non-header lines per page.
    :return: boolean indicating if OCR is needed.
    """
    lines = (ln.strip() for ln in content.splitlines())
    in_page = False
    other_content_count = 0
    saw_any_page = False
    for line in lines:
        if is_page_line(line):
            if in_page and other_content_count < line_count_threshold:
                logger.info(
                    f"Page with insufficient content: {other_content_count} lines (threshold: {line_count_threshold})"
                )
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
    if in_page and other_content_count < line_count_threshold:
        logger.info(
            f"Trailing page with insufficient content: {other_content_count} lines (threshold: {line_count_threshold})"
        )
        return True

    # If no pages were found, fall back to the regular behavior of checking whether
    # any content remains after removing common headers.
    if not saw_any_page:
        # Fallback: original missing-pages logic
        page_patterns = [
            r"Page\s+(\d+)",
            r"- (\d+) -",
            r"\[(\d+)\]",
            r"(\d+)\s*$",
        ]
        found_pages = set()
        for pattern in page_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                try:
                    page_num = int(match)
                    if 1 <= page_num <= page_count:
                        found_pages.add(page_num)
                except ValueError:
                    continue
        missing_pages = set(range(1, page_count + 1)) - found_pages
        if len(missing_pages) > 2:
            logger.info(
                f"Missing pages: {sorted(missing_pages)} out of expected {page_count}"
            )
            return True
        # If any non-header line exists, OCR is not needed
        for line in content.splitlines():
            if not is_doc_common_header(line.strip()):
                return False
        return True

    return False
