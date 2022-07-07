"""Defines domain-objects that encapsulate state without logic.
"""
from functools import total_ordering


@total_ordering
class Rating:
    """Store a template's rating."""

    mapping = {"critical": 0, "important": 1, "moderate": 2, "low": 3, "": 4}

    def __init__(self, rating):
        self.rating = rating

    def __lt__(self, other):
        return self.mapping.get(self.rating, 10) < self.mapping.get(other.rating, 10)

    def __eq__(self, other):
        return self.rating == other.rating

    def __str__(self):
        return self.rating


@total_ordering
class Priority:
    """Store the priority of this request's associated incident."""

    def __init__(self, prio):
        self.priority = int(prio)

    def __eq__(self, other):
        return self.priority == other.priority

    def __lt__(self, other):
        return self.priority > other.priority

    def __str__(self):
        return "{0}".format(self.priority)


class UnknownPriority(Priority):
    def __init__(self):
        self.priority = None

    def __eq__(self, other):
        return isinstance(other, UnknownPriority)

    def __lt__(self, other):
        return False

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "{0}".format(self.priority)
