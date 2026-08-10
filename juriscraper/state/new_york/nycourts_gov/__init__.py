"""
New York Court of Appeals Court-PASS scraper, parsers, and data structures.

The scraper stack is resolved on attribute access rather than at import time
(PEP 562), so that reading ``vocabularies`` -- which CourtListener does to build
its database choices -- does not pull in the parsers, the scraper, and jkent
behind them. ``from juriscraper.state.new_york.nycourts_gov import X`` behaves
exactly as it did.
"""

from importlib import import_module
from typing import TYPE_CHECKING, Any

_EXPORTS: dict[str, str] = {
    "NYCourtPassAttorney": ".models",
    "NYCourtPassDocket": ".models",
    "NYCourtPassDocketEntry": ".models",
    "NYCourtPassFile": ".models",
    "NYCourtPassIssue": ".models",
    "DocketDetailParser": ".parsers.docket_detail",
    "DocketResultsParser": ".parsers.docket_results",
    "FilingDetailParser": ".parsers.filing_detail",
    "NYCourtPassScraper": ".scraper",
}

if TYPE_CHECKING:
    from .models import (
        NYCourtPassAttorney,
        NYCourtPassDocket,
        NYCourtPassDocketEntry,
        NYCourtPassFile,
        NYCourtPassIssue,
    )
    from .parsers.docket_detail import DocketDetailParser
    from .parsers.docket_results import DocketResultsParser
    from .parsers.filing_detail import FilingDetailParser
    from .scraper import NYCourtPassScraper

__all__ = [
    "DocketDetailParser",
    "DocketResultsParser",
    "FilingDetailParser",
    "NYCourtPassAttorney",
    "NYCourtPassDocket",
    "NYCourtPassDocketEntry",
    "NYCourtPassFile",
    "NYCourtPassIssue",
    "NYCourtPassScraper",
]


def __getattr__(name: str) -> Any:
    """Import the module holding `name` the first time it is asked for."""
    module = _EXPORTS.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(import_module(module, __name__), name)


def __dir__() -> list[str]:
    return sorted(__all__)
