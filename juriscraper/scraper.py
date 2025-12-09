from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Scraper(Generic[T], ABC):
    @abstractmethod
    def _parse_text(self, text: str) -> None:
        pass

    @property
    @abstractmethod
    def data(self) -> T:
        pass
