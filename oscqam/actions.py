from functools import wraps
from .models import Group, User, Request, Template


class UninferableError(Exception):
    """Error to raise when the program should try to auto-infer some values, but
    can not do so due to ambiguity.

    """
    def __init__(self, msg):
        self.msg = msg


class OscAction(object):
    """Base class for actions that need to interface with the open build service.

    """
    def __init__(self, remote, user):
        self.remote = remote
        self.all_groups = Group.all(remote)
        self.user = User.by_name(self.remote, user)
        self.undo_stack = []

    def __call__(self, apiurl, **kwargs):
        pass

    def rollback(self):
        for action in self.undo_stack:
            action()


class ListAction(OscAction):
    def __call__(self):
        """Return all requests that match the parameters of the RequestAction.

        """
        qam_groups = self.user.qam_groups
        user_requests = set(Request.for_user(self.remote, self.user))
        group_requests = set(Request.open_for_groups(self.remote, qam_groups))
        all_requests = user_requests.union(group_requests)
        templates = [Template.for_request(req) for req in all_requests]
        return templates


class AssignAction(OscAction):
    def __init__(self, remote, user, request_id):
        super(AssignAction, self).__init__(remote, user)
        self.request = Request.by_id(self.remote, request_id)
    
    def __call__(self, group_to_replace=None):
        if group_to_replace:
            self.assign(group_to_replace)
        else:
            self.infer_group()

    def infer_group(self):
        """Based on the given user and request id search for a group that
        the user could do the review for.

        """
        user_groups = set(self.user.qam_groups)
        reviews = [review for review in self.request.review_list_open() if
                   review.review_type == Request.REVIEW_GROUP]
        open_groups = set([Group.for_name(self.remote, review.name) for review
                           in reviews])
        both = user_groups.intersection(open_groups)
        if not both:
            raise UninferableError("No matching qam-groups found for user.")
        else:
            if len(both) > 1:
                error = "User could review more than one group: %s" % both
                raise UninferableError(error)
            else:
                group = both.pop()
                # TODO: Ensure that the user actually wants this?
                self.assign(group)
        
    def assign(self, group):
        self.request.review_add(user=self.user)
        self.undo_stack.append(
            lambda: self.request.review_accept(user=self.user)
        )
        self.request.review_accept(group=group)
        self.undo_stack.append(
            lambda: self.request.review_reopen(group=group)
        )


        self.request.review_accept(user=self.user)
