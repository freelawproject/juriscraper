import logging

from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger()


class ErrorContextMixin:
    """Optional attributes that CourtListener reads to tag and group Sentry
    events, set through `attach_error_context`"""

    court_id: str | None = None
    url: str | None = None
    sentry_fingerprint: list[str] | None = None
    sentry_owner: str | None = None


def attach_error_context(
    exc: BaseException,
    court_id: str | None = None,
    url: str | None = None,
    fingerprint: list[str] | None = None,
    owner: str | None = None,
) -> BaseException:
    """Set `ErrorContextMixin` attributes on any exception; existing values win

    :return: the same exception, for `raise attach_error_context(...)`
    """
    values = {
        "court_id": court_id,
        "url": url,
        "sentry_fingerprint": fingerprint,
        "sentry_owner": owner,
    }
    for name, value in values.items():
        # must never replace the exception being handled
        try:
            if value is None or getattr(exc, name, None) is not None:
                continue
            setattr(exc, name, value)
        except Exception:
            continue
    return exc


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


class ParsingException(ErrorContextMixin, Exception):
    """Raised when parsing fails."""


class InsanityException(ErrorContextMixin, Exception):
    """Raised when data validation fails."""


class PacerLoginException(ErrorContextMixin, Exception):
    """Raised when the system cannot authenticate with PACER"""


class InvalidDocumentError(ErrorContextMixin, Exception):
    """Raised when the document got from `download_url` is invalid

    May be an error page that is undetected by `response.raise_for_status`
    or our `expected_content_type` controls. Proper place to raise this
    would be on `Site.cleanup_content`
    """


class AutoLoggingException(ErrorContextMixin, Exception):
    """Exception with defaults for logging, to be subclassed

    We log expected exceptions to better understand what went wrong.
    Subclasses that CourtListener reports itself log at WARNING, since ERROR
    logs reach Sentry too. The `fingerprint` is kept on
    `self.sentry_fingerprint` for that report.

    Other `logger` calls are just printed on the console when using a
    VerboseCommand with proper verbosity levels
    """

    logging_level = logging.DEBUG
    message = ""
    logger = logger

    def __init__(
        self,
        message: str = "",
        logger: logging.Logger | None = None,
        logging_level: int | None = None,
        fingerprint: list[str] | None = None,
        data: dict | None = None,
    ):
        if not message:
            message = self.message
        if not logger:
            logger = self.logger
        if not logging_level:
            logging_level = self.logging_level

        extra: dict[str, object] | None
        if fingerprint:
            extra = {"fingerprint": fingerprint}
        else:
            extra = None

        # pass custom data that an outer try/except block can access
        self.data = data
        self.sentry_fingerprint = fingerprint

        logger.log(logging_level, message, extra=extra)
        super().__init__(message)


class BadContentError(AutoLoggingException):
    """Parent class for errors raised when downloading binary content"""


class UnexpectedContentTypeError(BadContentError):
    """Occurs when the content received from the server has
    a different content type than the ones listed on
    site.expected_content_types
    """

    logging_level = logging.WARNING


class NoDownloadUrlError(BadContentError):
    """Occurs when a DeferredList fetcher fails."""

    logging_level = logging.WARNING


class EmptyFileError(BadContentError):
    """Occurs when the content of the response has lenght 0"""

    logging_level = logging.WARNING


class MergingError(AutoLoggingException):
    """Raised when metadata merging finds different values"""

    logging_level = logging.ERROR


class BotChallengeError(BadContentError):
    """Raised when the source serves a bot/captcha challenge page instead
    of the expected content (e.g. Radware Bot Manager, Cloudflare).

    Raising loudly prevents silently ingesting zero results, which would
    otherwise look like a successful scrape with no new opinions. As a
    `BadContentError`, a blocked document is skipped like any bad download.
    """

    logging_level = logging.WARNING
