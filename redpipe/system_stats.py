import threading
from os import getenv
from contextlib import contextmanager


ENABLE_REDPIPE_STATS = getenv('ENABLE_REDPIPE_STATS', 'false') == 'true'

threading_local = threading.local()
threading_local.futures_accessed = 0
threading_local.futures_created = 0
threading_local.futures_accessed_ids = set()


@contextmanager
def log_redpipe_stats(name: str, logger, pid):
    """
    Resets futures created and accessed counts before a function is called and
    then measures those values to report after
    """
    if not ENABLE_REDPIPE_STATS:
        yield
    else:
        threading_local.futures_accessed = 0
        threading_local.futures_created = 0
        threading_local.futures_accessed_ids = set()
        yield
        consumed = 0 if threading_local.futures_created == 0 else \
            threading_local.futures_accessed / threading_local.futures_created
        logging_data = {
            "pid": pid,
            "name": name,
            "futures_accessed": threading_local.futures_accessed,
            "futures_created": threading_local.futures_created,
            "Consumption Percentage": "{:.0%}".format(consumed)
        }
        logger.info("REDPIPE_STATS", **logging_data)
