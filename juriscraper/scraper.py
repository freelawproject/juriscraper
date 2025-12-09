from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Scraper(Generic[T], ABC):
    @abstractmethod
    def __init__(self, court_id: str):
        self.court_id: str = court_id

    @abstractmethod
    def _parse_text(self, text: str) -> None:
        pass

    @property
    @abstractmethod
    def data(self) -> T:
        pass
