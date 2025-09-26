"""Provides an abstract base class for reviewers."""

import abc


class Reviewer(metaclass=abc.ABCMeta):
    """Superclass for possible reviewer-classes."""

    @abc.abstractmethod
    def is_qam_group(self):
        """Checks if the reviewer is a QAM group.

        Returns:
            True if the reviewer is a QAM group, False otherwise.
        """
        pass
