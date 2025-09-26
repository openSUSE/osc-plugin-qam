"""Provides a class for interacting with groups on the remote."""

from functools import lru_cache

from ..models import Group


class GroupRemote:
    """Interacts with groups on the remote.

    Attributes:
        remote: A remote facade.
        endpoint: The API endpoint for groups.
    """

    def __init__(self, remote):
        """Initializes a GroupRemote.

        Args:
            remote: A remote facade.
        """
        self.remote = remote
        self.endpoint = "group"

    @lru_cache(maxsize=None)
    def all(self):
        """Gets all groups.

        Returns:
            A list of all Group objects.
        """
        group_entries = Group.parse_entry(self.remote, self.remote.get(self.endpoint))
        return group_entries

    def for_pattern(self, pattern):
        """Gets all groups that match a given pattern.

        Args:
            pattern: A compiled regular expression to match against group names.

        Returns:
            A list of matching Group objects.
        """
        return [group for group in self.all() if pattern.match(group.name)]

    @lru_cache(maxsize=None)
    def for_name(self, group_name):
        """Gets a group by name.

        Args:
            group_name: The name of the group to get.

        Returns:
            A Group object.

        Raises:
            AttributeError: If no group is found with the given name.
        """
        url = "/".join([self.endpoint, group_name])
        group = Group.parse(self.remote, self.remote.get(url))
        if group:
            return group[0]
        else:
            raise AttributeError("No group found for name: {0}".format(group_name))

    @lru_cache(maxsize=None)
    def for_user(self, user):
        """Gets all groups for a given user.

        Args:
            user: The user to get groups for.

        Returns:
            A list of Group objects.
        """
        params = {"login": user.login}
        group_entries = Group.parse_entry(
            self.remote, self.remote.get(self.endpoint, params)
        )
        groups = [self.for_name(g.name) for g in group_entries]
        return groups
