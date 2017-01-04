class BadLoginException(Exception):
    """The document could not be formed"""

    def __init__(self, message):
        Exception.__init__(self, message)
