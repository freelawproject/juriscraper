from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar, final

from juriscraper.abstract_parser import AbstractParser

_ParserInput = TypeVar("_ParserInput")
_ParserOutput = TypeVar("_ParserOutput")


class ParserValidationError(Exception):
    pass


class Parser(ABC, Generic[_ParserInput, _ParserOutput]):
    output: Optional[_ParserOutput]

    def __init__(self):
        self.output = None

    @final
    def parse(self, i: _ParserInput) -> _ParserOutput:
        if self.output is not None:
            return self.output
        output = self._parse(i)
        if output is None:
            raise ParserValidationError("Parser output cannot be None")
        if not self.validate(output):
            raise ParserValidationError("Parser output failed validation.")
        self.output = output
        return output

    def validate(self, _output: _ParserOutput) -> bool:
        return True

    @abstractmethod
    def _parse(self, i: _ParserInput) -> _ParserOutput:
        raise NotImplementedError


class LegacyParser(
    Generic[_ParserOutput],
    AbstractParser[_ParserOutput],
    Parser[str, _ParserOutput],
    ABC,
):
    def __init__(self, court_id: str):
        AbstractParser.__init__(self, court_id)
        Parser.__init__(self)

    @final
    def _parse_text(self, text: str) -> None:
        self.parse(text)

    @property
    @final
    def data(self) -> _ParserOutput:
        if self.output is None:
            raise ValueError("Input has not been parsed yet.")
        return self.output
