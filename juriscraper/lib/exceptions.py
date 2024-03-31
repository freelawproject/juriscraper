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


class DocketNotFound(JuriscraperException):
    """Use when a docket number request returns the file not found error page."""

    def __init__(self, message):
        super().__init__(self, message)


class DocketMissingJSON(JuriscraperException):
    """Use when a docket number request returns a JSONDecodeError."""

    def __init__(self, message):
        super().__init__(self, message)


class AccessDeniedError(JuriscraperException):
    """Raise when supremecourt.gov returns an 'Access Denied' page.

    <HTML><HEAD>
    <TITLE>Access Denied</TITLE>
    </HEAD><BODY>
    <H1>Access Denied</H1>

    You don't have permission to access "http&#58;&#47;&#47;www&#46;supremecourt&#46;gov&#47;docket&#47;docket&#46;aspx" on this server.<P>
    Reference&#32;&#35;18&#46;1c0f2417&#46;1709421040&#46;28130f66
    </BODY>
    </HTML>
    """
