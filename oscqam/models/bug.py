"""Represents a bug tracker issue."""

from .xmlfactorymixin import XmlFactoryMixin


class Bug(XmlFactoryMixin):
    """Represents a bug tracker issue.

    Attributes:
        tracker: The name of the bug tracker.
        id: The ID of the bug in the tracker.
    """

    # TODO: where we get tracker and ID ?
    def __str__(self):
        """Returns a string representation of the bug.

        Returns:
            A string in the format "tracker:id".
        """
        return "{0}:{1}".format(self.tracker, self.id)
