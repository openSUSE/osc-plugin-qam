from functools import lru_cache

from ..models import Group


class GroupRemote:
    def __init__(self, remote):
        self.remote = remote
        self.endpoint = "group"

    @lru_cache(maxsize=None)
    def all(self):
        group_entries = Group.parse_entry(self.remote, self.remote.get(self.endpoint))
        return group_entries

    def for_pattern(self, pattern):
        return [group for group in self.all() if pattern.match(group.name)]

    @lru_cache(maxsize=None)
    def for_name(self, group_name):
        url = "/".join([self.endpoint, group_name])
        group = Group.parse(self.remote, self.remote.get(url))
        if group:
            return group[0]
        else:
            raise AttributeError("No group found for name: {0}".format(group_name))

    @lru_cache(maxsize=None)
    def for_user(self, user):
        params = {"login": user.login}
        group_entries = Group.parse_entry(
            self.remote, self.remote.get(self.endpoint, params)
        )
        groups = [self.for_name(g.name) for g in group_entries]
        return groups
