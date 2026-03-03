from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar, final

from juriscraper.state.network_driver import NetworkDriver

_ParserInput = TypeVar("_ParserInput")
_ParserOutput = TypeVar("_ParserOutput")


class ParserValidationError(Exception):
    pass


class Parser(ABC, Generic[_ParserOutput, _ParserInput]):
    data: Optional[_ParserOutput]

    def __init__(self):
        self.data = None

    @final
    def __call__(self, i: _ParserInput) -> _ParserOutput:
        if self.data is not None:
            return self.data
        data = self.parse(i)
        if data is None:
            raise ParserValidationError("Parser output cannot be None")
        if not self.validate(data):
            raise ParserValidationError("Parser output failed validation.")
        self.data = data
        return data

    @abstractmethod
    def validate(self, _data: _ParserOutput) -> bool:
        return True

    @abstractmethod
    def parse(self, i: _ParserInput) -> _ParserOutput:
        raise NotImplementedError


_ScraperNetworkDriver = TypeVar("_ScraperNetworkDriver", bound=NetworkDriver)


class Scraper(ABC, Generic[_ScraperNetworkDriver]):
    driver: _ScraperNetworkDriver

    def __init__(self, driver: _ScraperNetworkDriver) -> None:
        self.driver = driver
