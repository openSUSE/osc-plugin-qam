from functools import wraps
from models import Group, User, Request


class RemoteAction(object):
    def __init__(self):
        pass

    def __call__(self, apiurl, **kwargs):
        pass

    def rollback(self, *args, **kwargs):
        pass


class AssignAction(RemoteAction):
    def __init__(self, user, group, request):
        """Action to assign a user to a request.

        Will ensure that the action is atomically performed or not performed
        at all.

        """
        super(AssignAction, self).__init__(apiurl)
        self.user = user
        self.group = group
        self.request = request

    def __call__(self):
        self.request.add(self.user)
        self.request.accept(self.group)

    def rollback(self):
        self.request.reopen(self.group)
        self.request.accept(self.user)


class RequestAction(object):
    def __init__(self, remote, user, requestid):
        self.remote = remote
        self.all_groups = Group.all(remote)
        self.user = User.by_name(self.remote, user)
        self.request = Request.by_id(self.remote, requestid)

    def list(self):
        requests = Request.for_user(self.remote, self.user)

    def assign(self):
        action = AssignAction(self.user, self.group, self.request)
        action()

    def unassign(self):
        pass

    def approve(self):
        pass

    def reject(self):
        pass

    def comment(self):
        pass

    def history(self):
        pass
