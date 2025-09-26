"""Defines domain-objects that encapsulate state without logic."""

from functools import total_ordering


@total_ordering
class Rating:
    """Store a template's rating.

    Ratings are ordered from most to least important.

    Attributes:
        mapping: A dictionary mapping rating strings to integer values.
        rating: The rating string.
    """

    mapping = {"critical": 0, "important": 1, "moderate": 2, "low": 3, "": 4}

    def __init__(self, rating):
        """Initializes a Rating.

        Args:
            rating: The rating string.
        """
        self.rating = rating

    def __lt__(self, other):
        """Compares two ratings.

        Args:
            other: The other rating to compare to.

        Returns:
            True if this rating is less than the other, False otherwise.
        """
        return self.mapping.get(self.rating, 10) < self.mapping.get(other.rating, 10)

    def __eq__(self, other):
        """Checks if two ratings are equal.

        Args:
            other: The other rating to compare to.

        Returns:
            True if the ratings are equal, False otherwise.
        """
        return self.rating == other.rating

    def __str__(self):
        """Returns a string representation of the rating.

        Returns:
            The rating string.
        """
        return self.rating


@total_ordering
class Priority:
    """Store the priority of this request's associated incident.

    Attributes:
        priority: The integer priority value.
    """

    def __init__(self, prio):
        """Initializes a Priority.

        Args:
            prio: The priority value.
        """
        self.priority = int(prio)

    def __eq__(self, other):
        """Checks if two priorities are equal.

        Args:
            other: The other priority to compare to.

        Returns:
            True if the priorities are equal, False otherwise.
        """
        return self.priority == other.priority

    def __lt__(self, other):
        """Compares two priorities.

        Higher integer value means lower priority.

        Args:
            other: The other priority to compare to.

        Returns:
            True if this priority is less than the other, False otherwise.
        """
        return self.priority > other.priority

    def __str__(self):
        """Returns a string representation of the priority.

        Returns:
            The priority as a string.
        """
        return "{0}".format(self.priority)


class UnknownPriority(Priority):
    """Represents an unknown priority.

    This is a subclass of Priority that is used when the priority of an
    incident cannot be determined. It is always considered to be the lowest
    priority.

    Attributes:
        priority: Always None for UnknownPriority.
    """

    def __init__(self):
        """Initializes an UnknownPriority."""
        self.priority = None

    def __eq__(self, other):
        """Checks if this is equal to another object.

        Args:
            other: The other object to compare to.

        Returns:
            True if the other object is also an UnknownPriority, False otherwise.
        """
        return isinstance(other, UnknownPriority)

    def __lt__(self, other):
        """Compares this to another object.

        An UnknownPriority is never less than anything.

        Args:
            other: The other object to compare to.

        Returns:
            False.
        """
        return False

    def __str__(self):
        """Returns a string representation of the priority.

        Returns:
            The string "None".
        """
        return "{0}".format(self.priority)
