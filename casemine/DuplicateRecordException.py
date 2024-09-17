class DuplicateRecordException(Exception):
    """Exception raised for duplicate record errors."""
    def __init__(        self,message: str):
        super().__init__(message)
