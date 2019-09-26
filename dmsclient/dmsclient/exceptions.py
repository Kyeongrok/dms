class DMSClientException(Exception):
    """
    This is a custom DMSClientException Exception class to better handle
    errors that DMSClient can return.
    It includes the original error message from Elasticsearch (es_message) and the
    HTTP status code returned (http_status_code).
    """

    def __init__(self, message, status_code=None):
        super(DMSClientException, self).__init__(message)
        self.message = message
        self.status_code = status_code

    @classmethod
    def from_exception(cls, exception, message=None):
        message = message or ''
        if hasattr(exception, 'error'):
            message += ': %s' % (exception.error,)
        if hasattr(exception, 'info') and 'error' in exception.info:
            message += ': %s' % (exception.info['error'],)
        if not message:
            message = str(exception)
        status_code = None
        if hasattr(exception, 'status_code'):
            status_code = exception.status_code
        return cls(message,
                   status_code=status_code)


class DMSDocumentNotFoundError(DMSClientException):
    """ Exception representing a missing entry for a particular resource"""

    def __init__(self, message='Could not find document'):
        super(DMSDocumentNotFoundError, self).__init__(message, status_code=404)


class DMSConflictError(DMSClientException):
    """ Exception representing a conflict in the DMS. Most likely when trying
    to create a document with an ID that already exists """


class DMSInvalidFormat(DMSClientException):
    """ Exception representing an invalid format in any of the resources """
