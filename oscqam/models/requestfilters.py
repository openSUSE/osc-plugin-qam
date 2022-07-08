import abc


class RequestFilter(metaclass=abc.ABCMeta):
    """Methods that allow filtering on requests."""

    @abc.abstractmethod
    def maintenance_requests(self, requests):
        pass

    @classmethod
    def for_remote(cls, remote):
        """Return the correct Filter for the given remote."""
        if "opensuse" in remote.remote:
            return OBSRequestFilter()
        else:
            return IBSRequestFilter()


class OBSRequestFilter(RequestFilter):
    PREFIX = "openSUSE:Maintenance"

    def maintenance_requests(self, requests):
        return [r for r in requests if self.PREFIX in r.src_project]


class IBSRequestFilter(RequestFilter):
    PREFIX = "SUSE:Maintenance"

    def maintenance_requests(self, requests):
        return [r for r in requests if self.PREFIX in r.src_project]
