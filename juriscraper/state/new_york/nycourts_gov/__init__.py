"""
New York Court of Appeals Court-PASS scraper, parsers, and data structures.
"""

from .models import (
    NYCourtPassAttorney,
    NYCourtPassDocket,
    NYCourtPassDocketEntry,
    NYCourtPassFile,
)
from .parsers.docket_detail import DocketDetailParser
from .parsers.docket_results import DocketResultsParser
from .parsers.filing_detail import FilingDetailParser
from .scraper import NYCourtPassScraper

__all__ = [
    "NYCourtPassAttorney",
    "NYCourtPassDocket",
    "NYCourtPassDocketEntry",
    "NYCourtPassFile",
    "DocketDetailParser",
    "DocketResultsParser",
    "FilingDetailParser",
    "NYCourtPassScraper",
]
