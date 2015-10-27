"""Defines domain-objects that encapsulate state without logic.
"""
from .compat import total_ordering


@total_ordering
class Rating(object):
    """Store a template's rating.
    """
    mapping = {
        'critical': 0,
        'important': 1,
        'moderate': 2,
        'low': 3,
        '': 4
    }

    def __init__(self, rating):
        self.rating = rating

    def __lt__(self, other):
        return (self.mapping.get(self.rating, 10) <
                self.mapping.get(other.rating, 10))

    def __eq__(self, other):
        return self.rating == other.rating

    def __str__(self):
        return self.rating
