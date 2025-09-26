"""Provides a class for interacting with users on the remote."""

from functools import lru_cache

from ..models import User


class UserRemote:
    """Interacts with users on the remote.

    Attributes:
        remote: A remote facade.
        endpoint: The API endpoint for users.
    """

    def __init__(self, remote):
        """Initializes a UserRemote.

        Args:
            remote: A remote facade.
        """
        self.remote = remote
        self.endpoint = "person"

    @lru_cache(maxsize=None)
    def by_name(self, name):
        """Gets a user by name.

        Args:
            name: The name of the user to get.

        Returns:
            A User object.

        Raises:
            AttributeError: If the user is not found.
        """
        url = "/".join([self.endpoint, name])
        users = User.parse(self.remote, self.remote.get(url))
        if users:
            return users[0]
        raise AttributeError("User not found.")
