from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class AbstractParser(Generic[T], ABC):
    """Abstract base class, which all scrapers should inherit from."""

    @abstractmethod
    def __init__(self, court_id: str):
        self.court_id: str = court_id

    @abstractmethod
    def _parse_text(self, text: str) -> None:
        """Ingest some arbitrary text and prepare it to be parsed by the data() method."""
        pass

    @property
    @abstractmethod
    def data(self) -> T:
        """Parse the last text ingested by _parse_text()."""
        pass
