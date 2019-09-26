from elasticsearch import ElasticsearchException, TransportError
from retrying import retry

from dmsclient.exceptions import DMSClientException, DMSConflictError


def elasticsearch():
    """
    A decorator that syncs cluster configuration and catches Elasticsearch exceptions
    thrown by the decorated function and converts them to library-specific exceptions.

    Notes:
      Caught exceptions are re-raised.
    Returns:
      A decorator that catches Elasticsearch exceptions thrown by decorated functions.
    Raises:
      Nothing. The decorator will re-raise exceptions caught by the decorated
      function.
    """

    def decorator(func):
        def wrapper(*args, **kwds):
            sync = kwds.pop('sync', True)
            retries = kwds.pop('retries', 0)

            if sync:
                # Try to sync cluster information
                args[0].client.sync_cluster_config()

            @retry(stop_max_attempt_number=retries, wait_fixed=1000)
            def inner_wrapper(*args, **kwds):
                try:
                    return func(*args, **kwds)
                except TransportError as e:
                    if e.status_code == 409:
                        raise DMSConflictError.from_exception(e)
                    raise DMSClientException.from_exception(e)
                except ElasticsearchException as e:
                    raise DMSClientException.from_exception(e)

            return inner_wrapper(*args, **kwds)
        return wrapper
    return decorator
