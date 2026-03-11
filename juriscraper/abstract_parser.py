from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar, final


class ParserValidationError(Exception):
    """Exception raised when a parser fails the validation step."""

    pass


_ParserInput = TypeVar("_ParserInput")
_ParserOutput = TypeVar("_ParserOutput")


class Parser(ABC, Generic[_ParserInput, _ParserOutput]):
    """Abstract parser class with a nicer interface than existing parsers."""

    output: Optional[_ParserOutput]

    def __init__(self):
        self.output = None

    @final
    def parse(self, i: _ParserInput) -> _ParserOutput:
        """
        Parse and validate the input, raising a ParserValidationError if
        validation fails.

        :param i: Input to parse.

        :raises ParserValidationError: If validation fails.

        :return: Parsed input.
        """
        if self.output is not None:
            return self.output
        output = self._parse(i)
        if not self.validate(output):
            raise ParserValidationError("Parser output failed validation.")
        self.output = output
        return output

    def validate(self, _output: _ParserOutput) -> bool:
        """
        Placeholder validation function. Is a no-op in the base class, but
        can be overridden by subclasses.
        """
        return True

    @abstractmethod
    def _parse(self, i: _ParserInput) -> _ParserOutput:
        """
        Internal parsing method which all subclasses must implement. Used in
        the public parse method to produce the output before validation.

        :param i: Input to parse.
        :return: Parsed input.
        """
        raise NotImplementedError


T = TypeVar("T")


class AbstractParser(Generic[_ParserOutput], Parser[str, _ParserOutput], ABC):
    """Abstract base class, which all scrapers should inherit from."""

    def __init__(self, court_id: str):
        self.court_id: str = court_id
        Parser.__init__(self)

    def _parse_text(self, text: str) -> None:
        """Ingest some arbitrary text and prepare it to be parsed by the data() method."""
        self.parse(text)

    @property
    def data(self) -> _ParserOutput:
        """Parse the last text ingested by _parse_text()."""
        if self.output is None:
            raise ParserValidationError("Input has not been parsed yet.")
        return self.output
