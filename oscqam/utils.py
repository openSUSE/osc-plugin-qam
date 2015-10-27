from functools import wraps
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def memoize(func):
    """Memoizes a function to reduce repetitive calling costs.

    To work the decorated function must have hashable arguments.
    """
    cache = {}
    @wraps(func)
    def wrapped(*args, **kwargs):
        sorted_keys = sorted(kwargs.keys())
        arguments = (frozenset(args),
                     frozenset([(k, kwargs[k]) for k in sorted_keys]))
        if arguments in cache:
            return cache[arguments]
        result = func(*args, **kwargs)
        cache[arguments] = result
        return result
    return wrapped