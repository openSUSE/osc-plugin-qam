from functools import wraps
from .models import Group, User, Request, Template


class RemoteAction(object):
    def __init__(self, remote, user):
        self.remote = remote
        self.all_groups = Group.all(remote)
        self.user = User.by_name(self.remote, user)

    def __call__(self, apiurl, **kwargs):
        pass

    def rollback(self, *args, **kwargs):
        pass


class ListAction(RemoteAction):
    def __call__(self):
        """Return all requests that match the parameters of thie RequestAction.

        """
        qam_groups = self.user.qam_groups
        user_requests = set(Request.for_user(self.remote, self.user))
        group_requests = set(Request.open_for_groups(self.remote, qam_groups))
        all_requests = user_requests.union(group_requests)
        templates = [Template.for_request(req) for req in all_requests]
        return templates


class AssignAction(RemoteAction):
    def __init__(self, remote, user, group, request):
        """Action to assign a user to a request.

        Will ensure that the action is atomically performed or not performed
        at all.

        """
        super(AssignAction, self).__init__(remote, user)
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
        self.request = Request.by_id(self.remote, requestid)

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
