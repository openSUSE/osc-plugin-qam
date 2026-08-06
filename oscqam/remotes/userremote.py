"""Provides a class for interacting with users on the remote."""

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
        self._by_name_cache = {}

    def by_name(self, name):
        """Gets a user by name.

        Args:
            name: The name of the user to get.

        Returns:
            A User object.

        Raises:
            AttributeError: If the user is not found.
        """
        if name not in self._by_name_cache:
            url = f"{self.endpoint}/{name}"
            users = User.parse(self.remote, self.remote.get(url))
            if not users:
                raise AttributeError("User not found.")
            self._by_name_cache[name] = users[0]
        return self._by_name_cache[name]
