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


# Court-PASS writes a consolidated caption as several captions separated by a
# horizontal rule, and *escapes* the markup for it -- the Title element's text
# literally contains ``&lt;br /&gt;-------------&lt;br /&gt;``. Unescaped by the
# HTML parse, that reaches the model as a literal ``<br />`` in the case name.
_ESCAPED_BREAK = re.compile(r"<\s*br\s*/?\s*>", re.I)
#: the rule itself, as a run of hyphens or underscores on its own
_CAPTION_RULE = re.compile(r"[-_]{3,}")


def clean_case_title(parts: list[str]) -> str:
    """Join a Title/caption element's text nodes into one case name.

    Folds the escaped ``<br />`` markup and the hyphen rules Court-PASS uses to
    separate the captions of consolidated companion cases into a single ``; ``,
    so the name reads as a caption rather than carrying the page's typography.
    Whitespace, including the newlines the site indents captions with, is
    collapsed.
    """
    joined = " ".join(part.strip() for part in parts if part.strip())
    joined = _ESCAPED_BREAK.sub(" ", joined)
    joined = _CAPTION_RULE.sub(";", joined)
    # a rule sat between two breaks, so the fold above leaves ` ; ` runs, and
    # the caption it ended already carried its own comma
    joined = re.sub(r"\s*(?:[,;]\s*)*;(?:\s*[,;])*\s*", "; ", joined)
    # Court-PASS leaves a doubled comma where a party name is blank
    joined = re.sub(r",\s*,+", ",", joined)
    return re.sub(r"\s+", " ", joined).strip(" ;,")
