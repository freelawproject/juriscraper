"""
Court-PASS page parsers for the New York Court of Appeals scraper.
"""

from .docket_detail import DocketDetailParser
from .docket_results import DocketResultsParser
from .filing_detail import FilingDetailParser

__all__ = [
    "DocketDetailParser",
    "DocketResultsParser",
    "FilingDetailParser",
]
