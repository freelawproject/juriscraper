from juriscraper.lib.log_tools import make_default_logger


class JuriscraperException(Exception):
    """
    Base class for Juriscraper custom exceptions
    """

    logger = make_default_logger()


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


class BadContentError(JuriscraperException):
    """Parent class for errors raised when downloading binary content"""


class UnexpectedContentTypeError(BadContentError):
    """Occurs when the content received from the server has
    a different content type than the ones listed on
    site.expected_content_types
    """

    def __init__(self, message: str, fingerprint: str = None):
        self.fingerprint = fingerprint
        log_message = message
        if fingerprint:
            log_message += f" | Fingerprint: {fingerprint}"
        self.logger.error(log_message)


class NoDownloadUrlError(BadContentError):
    """Occurs when a DeferredList fetcher fails."""

    def __init__(self, message: str):
        self.logger.error(message)


class EmptyFileError(BadContentError):
    """Occurs when the content of the response has lenght 0"""

    def __init__(self, message: str):
        self.logger.error(message)
