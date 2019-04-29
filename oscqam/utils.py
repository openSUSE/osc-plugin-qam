
from .compat import PY3
import ssl
from functools import wraps

if PY3:
    from urllib.request import urlopen
    from urllib.error import HTTPError
else:
    from urllib2 import urlopen
    from urllib2 import HTTPError

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


def https(url):
    try:
        ctx = ssl.create_default_context()
        return urlopen(url, context=ctx)
    except HTTPError:
        return None
