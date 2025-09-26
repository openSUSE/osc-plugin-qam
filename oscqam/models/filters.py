"""Provides filters for groups based on the remote."""

import abc


class GroupFilter(metaclass=abc.ABCMeta):
    """Methods that allow filtering on groups."""

    @abc.abstractmethod
    def is_qam_group(self):
        """Checks if a group is a QAM group.

        This method must be implemented by subclasses.
        """
        pass

    @classmethod
    def for_remote(cls, remote):
        """Return the correct Filter for the given remote.

        Args:
            remote: The remote to get the filter for.

        Returns:
            A GroupFilter object.
        """
        if "opensuse" in remote.remote:
            return OBSGroupFilter()
        else:
            return IBSGroupFilter()


class OBSGroupFilter(GroupFilter):
    """Methods that allow filtering on groups from OBS."""

    def is_qam_group(self, group):
        """Checks if a group is a QAM group in OBS.

        Args:
            group: The group to check.

        Returns:
            True if the group is a QAM group, False otherwise.
        """
        return group.name.startswith("qa-opensuse.org")


class IBSGroupFilter(GroupFilter):
    """Methods that allow filtering on groups from IBS.

    Attributes:
        IGNORED_GROUPS: A list of groups to ignore.
    """

    IGNORED_GROUPS = ["qam-auto", "qam-openqa"]

    def is_qam_group(self, group):
        """Checks if a group is a QAM group in IBS.

        Args:
            group: The group to check.

        Returns:
            True if the group is a QAM group, False otherwise.
        """
        return group.name.startswith("qam") and group.name not in self.IGNORED_GROUPS
