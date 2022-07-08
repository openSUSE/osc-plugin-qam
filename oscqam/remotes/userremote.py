from functools import lru_cache

from ..models import User


class UserRemote:
    def __init__(self, remote):
        self.remote = remote
        self.endpoint = "person"

    @lru_cache(maxsize=None)
    def by_name(self, name):
        url = "/".join([self.endpoint, name])
        users = User.parse(self.remote, self.remote.get(url))
        if users:
            return users[0]
        raise AttributeError("User not found.")
