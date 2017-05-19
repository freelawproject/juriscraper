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
