import abc


class GroupFilter(metaclass=abc.ABCMeta):
    """Methods that allow filtering on groups."""

    @abc.abstractmethod
    def is_qam_group(self):
        pass

    @classmethod
    def for_remote(cls, remote):
        """Return the correct Filter for the given remote."""
        if "opensuse" in remote.remote:
            return OBSGroupFilter()
        else:
            return IBSGroupFilter()


class OBSGroupFilter(GroupFilter):
    """Methods that allow filtering on groups from OBS."""

    def is_qam_group(self, group):
        return group.name.startswith("qa-opensuse.org")


class IBSGroupFilter(GroupFilter):
    IGNORED_GROUPS = ["qam-auto", "qam-openqa"]

    """Methods that allow filtering on groups from IBS."""

    def is_qam_group(self, group):
        return group.name.startswith("qam") and group.name not in self.IGNORED_GROUPS
