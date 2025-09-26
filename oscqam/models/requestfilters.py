"""Provides filters for requests based on the remote."""

import abc


class RequestFilter(metaclass=abc.ABCMeta):
    """Methods that allow filtering on requests."""

    @abc.abstractmethod
    def maintenance_requests(self, requests):
        """Filters a list of requests to only include maintenance requests.

        This method must be implemented by subclasses.

        Args:
            requests: A list of requests to filter.

        Returns:
            A list of maintenance requests.
        """
        pass

    @classmethod
    def for_remote(cls, remote):
        """Return the correct Filter for the given remote.

        Args:
            remote: The remote to get the filter for.

        Returns:
            A RequestFilter object.
        """
        if "opensuse" in remote.remote:
            return OBSRequestFilter()
        else:
            return IBSRequestFilter()


class OBSRequestFilter(RequestFilter):
    """Filters requests for OBS.

    Attributes:
        PREFIX: The prefix for maintenance projects in OBS.
    """

    PREFIX = "openSUSE:Maintenance"

    def maintenance_requests(self, requests):
        """Filters a list of requests to only include maintenance requests.

        Args:
            requests: A list of requests to filter.

        Returns:
            A list of maintenance requests.
        """
        return [r for r in requests if self.PREFIX in r.src_project]


class IBSRequestFilter(RequestFilter):
    """Filters requests for IBS.

    Attributes:
        PREFIX: The prefix for maintenance projects in IBS.
    """

    PREFIX = "SUSE:Maintenance"

    def maintenance_requests(self, requests):
        """Filters a list of requests to only include maintenance requests.

        Args:
            requests: A list of requests to filter.

        Returns:
            A list of maintenance requests.
        """
        return [r for r in requests if self.PREFIX in r.src_project]
