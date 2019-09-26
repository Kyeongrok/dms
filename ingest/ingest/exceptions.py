class IngestException(Exception):
    """
    This is a custom IngestException Exception class to better handle
    errors that the ingest program can return.
    It includes the original error message and the
    exit code to be returned.
    """

    def __init__(self, message, exit_code=1):
        super(IngestException, self).__init__(message)
        self.message = message
        self.exit_code = exit_code


class EgestTruncatedError(IngestException):
    """ Exception representing a truncated egestion"""

    def __init__(self, message='Egestion completed successfully but the result was truncated'):
        super(EgestTruncatedError, self).__init__(message, exit_code=100)
