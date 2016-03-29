"""This module provides required backports for older python versions.
"""
from collections import namedtuple
import httplib
try:
    import requests
    imp_requests = True
except ImportError:
    imp_requests = False


def total_ordering(cls):
    """Class decorator that fills in missing ordering methods

    Verbatim copy of python 2.7.8 stdlib!
    """
    convert = {
        '__lt__': [
            ('__gt__',
                lambda self, other: not (self < other or self == other)),
            ('__le__',
                lambda self, other: self < other or self == other),
            ('__ge__',
                lambda self, other: not self < other)
        ],
        '__le__': [
            ('__ge__',
                lambda self, other: not self <= other or self == other),
            ('__lt__',
                lambda self, other: self <= other and not self == other),
            ('__gt__',
                lambda self, other: not self <= other)
        ],
        '__gt__': [
            ('__lt__',
                lambda self, other: not (self > other or self == other)),
            ('__ge__',
                lambda self, other: self > other or self == other),
            ('__le__',
                lambda self, other: not self > other)
        ],
        '__ge__': [
            ('__le__',
                lambda self, other: (not self >= other) or self == other),
            ('__gt__',
                lambda self, other: self >= other and not self == other),
            ('__lt__',
                lambda self, other: not self >= other)
        ]
    }
    roots = set(dir(cls)) & set(convert)
    if not roots:
        raise ValueError('must define at least one ordering operation: < > <= >=')
    root = max(roots)       # prefer __lt__ to __le__ to __gt__ to __ge__
    for opname, opfunc in convert[root]:
        if opname not in roots:
            opfunc.__name__ = opname
            opfunc.__doc__ = getattr(int, opname).__doc__
            setattr(cls, opname, opfunc)
    return cls


def https26(url):
    if not imp_requests:
        raise AttributeError("Requests library not found, but required for 2.6")
    response = requests.get(url)
    return response.text.splitlines()
