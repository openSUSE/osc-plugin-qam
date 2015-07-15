try:
    from functools import total_ordering
except ImportError:
    from oscqam.backports import total_ordering
