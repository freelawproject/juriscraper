import logging
from typing import Optional

from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger()


class JuriscraperException(Exception):
    """
    Base class for Juriscraper custom exceptions
    """

    logger = logger


class SkipRowError(JuriscraperException):
    """
    Raise when a row or record has to be skipped
    For example, when collecting opinions and finding an order
    """

    def __init__(self, message: str):
        self.logger.debug(message)


class SlownessException(Exception):
    """Raised when things are too slow."""

    def __init__(self, message):
        Exception.__init__(self, message)


class ParsingException(Exception):
    """Raised when parsing fails."""

    def __init__(self, message):
        Exception.__init__(self, message)


class InsanityException(Exception):
    """Raised when data validation fails."""

    def __init__(self, message):
        Exception.__init__(self, message)


class PacerLoginException(Exception):
    """Raised when the system cannot authenticate with PACER"""

    def __init__(self, message):
        Exception.__init__(self, message)


class InvalidDocumentError(Exception):
    """Raised when the document got from `download_url` is invalid

    May be an error page that is undetected by `response.raise_for_status`
    or our `expected_content_type` controls. Proper place to raise this
    would be on `Site.cleanup_content`
    """


class AutoLoggingException(Exception):
    """Exception with defaults for logging, to be subclassed

    We log expected exceptions to better understand what went wrong
    Logger calls with level `logging.ERROR` are sent to Sentry, and
    it's useful to send a `fingerprint` to force a specific grouping by court

    Other `logger` calls are just printed on the console when using a
    VerboseCommand with proper verbosity levels
    """

    logging_level = logging.DEBUG
    message = ""
    logger = logger

    def __init__(
        self,
        message: str = "",
        logger: Optional[logging.Logger] = None,
        logging_level: Optional[int] = None,
        fingerprint: Optional[list[str]] = None,
        data: Optional[dict] = None,
    ):
        if not message:
            message = self.message
        if not logger:
            logger = self.logger
        if not logging_level:
            logging_level = self.logging_level

        log_kwargs = {}
        if fingerprint:
            log_kwargs["extra"] = {"fingerprint": fingerprint}

        # pass custom data that an outer try/except block can access
        self.data = data

        logger.log(logging_level, message, **log_kwargs)
        super().__init__(message)


class BadContentError(AutoLoggingException):
    """Parent class for errors raised when downloading binary content"""


class UnexpectedContentTypeError(BadContentError):
    """Occurs when the content received from the server has
    a different content type than the ones listed on
    site.expected_content_types
    """

    logging_level = logging.ERROR


class NoDownloadUrlError(BadContentError):
    """Occurs when a DeferredList fetcher fails."""

    logging_level = logging.ERROR


class EmptyFileError(BadContentError):
    """Occurs when the content of the response has lenght 0"""

    logging_level = logging.ERROR


class MergingError(AutoLoggingException):
    """Raised when metadata merging finds different values"""

    logging_level = logging.ERROR
