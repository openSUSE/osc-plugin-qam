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
        """Return all requests that match the parameters of the RequestAction.

        """
        qam_groups = self.user.qam_groups
        user_requests = set(Request.for_user(self.remote, self.user))
        group_requests = set(Request.open_for_groups(self.remote, qam_groups))
        all_requests = user_requests.union(group_requests)
        templates = [Template.for_request(req) for req in all_requests]
        return templates


class AssignAction(RemoteAction):
    def __init__(self, remote, user, request_id):
        super(AssignAction, self).__init__(remote, user)
        self.request = Request.by_id(self.remote, request_id)
    
    def __call__(self, group_to_replace=None):
        if group_to_replace:
            pass
            # Easy we were told what group to assign.
        else:
            self.infer_group()

    def infer_group(self):
        qam_groups = set(self.user.qam_groups)
        reviews = [review for review in self.request.review_list_open() if
                   review.review_type == Request.REVIEW_GROUP]
        open_groups = set([Group.for_name(self.remote, review.name) for review
                           in reviews])
        both = qam_groups.intersection(open_groups)
        if not both:
            return
        else:
            if len(both) > 1:
                # TODO: Too many groups possible: as for clarification.
                pass
            else:
                group = both.pop()
                # TODO: Ensure that the user actually wants this?
                self.assign(group)
        
    def assign(self, group):
        self.request.review_add(user=self.user)
        self.request.review_accept(group=group)

    def rollback(self):
        self.request.review_reopen(self.group)
        self.request.review_accept(user=self.user)


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
