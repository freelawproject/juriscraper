"""Shared helpers for the Court-PASS page parsers."""

from __future__ import annotations

import re
from datetime import date, datetime


def _parse_date_mdy(text: str | None) -> date | None:
    """Parse MM/DD/YYYY date strings emitted by Court-PASS."""
    if not text:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%m/%d/%Y").date()
    except ValueError:
        return None


# Court-PASS occasionally emits a PDF-derived font marker —
# ``<style pdffontname=...>`` with NO closing tag — inside
# ``<p class="case-issues-text">``. lxml treats ``<style>`` as raw text and
# extends it to the document-level ``</style>`` near ``</html>``, swallowing
# the gvFiles table and the "no files" marker into the style element. Dropping
# the bogus open tag (its content is the citation that belongs inline) lets the
# page parse normally, so downstream parsers can assume a clean DOM. Applied
# as the ``@step(preprocess=...)`` hook on the two filing-detail steps.
_PDF_STYLE_RE = re.compile(r"<style[^>]*\bpdffontname\b[^>]*>", re.I)


def repair_pdffont_leakage(text: str) -> str:
    """Strip Court-PASS's unclosed ``<style pdffontname=...>`` font markers."""
    return _PDF_STYLE_RE.sub("", text)
