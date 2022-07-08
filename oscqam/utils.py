from itertools import groupby
import ssl
from urllib.error import HTTPError
from urllib.request import urlopen


def https(url):
    try:
        ctx = ssl.create_default_context()
        return urlopen(url, context=ctx)
    except HTTPError:
        return None


def multi_level_sort(xs, criteria):
    """Sort the given collection based on multiple criteria.
    The criteria will be sorted by in the given order, whereas each group
    from the first criteria will be sorted by the second criteria and so forth.

    :param xs: Iterable of objects.
    :type xs: [a]

    :param criteria: Iterable of extractor functions.
    :type criteria: [a -> b]

    """
    if not criteria:
        return xs
    extractor = criteria[-1]
    xss = sorted(xs, key=extractor)
    grouped = groupby(xss, extractor)
    subsorts = (multi_level_sort(list(value), criteria[:-1]) for _, value in grouped)
    return [s for sub in subsorts for s in sub]
