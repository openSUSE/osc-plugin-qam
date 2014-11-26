from __future__ import print_function
from functools import wraps
from .models import Group, User, Request, Template, RemoteError


class ActionError(Exception):
    """General error to raise when an error occurred while performing one of the
    actions.

    """
    def __init__(self, msg):
        self.msg = msg


class UninferableError(ActionError):
    """Error to raise when the program should try to auto-infer some values, but
    can not do so due to ambiguity.

    """


class OscAction(object):
    """Base class for actions that need to interface with the open build service.

    """
    def __init__(self, remote, user):
        self.remote = remote
        self.all_groups = Group.all(remote)
        self.user = User.by_name(self.remote, user)
        self.undo_stack = []

    def __call__(self, *args, **kwargs):
        """Will attempt the encapsulated action and call the rollback function if an
        Error is encountered.

        """
        try:
            return self.action(*args, **kwargs)
        except RemoteError:
            self.rollback()

    def action(self, *args, **kwargs):
        pass

    def rollback(self):
        for action in self.undo_stack:
            action()


class ListAction(OscAction):
    def action(self):
        """Return all reviews that match the parameters of the RequestAction.

        """
        qam_groups = self.user.qam_groups
        user_requests = set(Request.for_user(self.remote, self.user))
        group_requests = set(Request.open_for_groups(self.remote, qam_groups))
        all_requests = user_requests.union(group_requests)
        templates = [Template.for_request(req) for req in all_requests]
        return templates


class AssignAction(OscAction):
    ASSIGN_USER_MSG = ("Will assign {user} to {group} for {request}.")
    AUTO_INFER_MSG = "Found a possible group: {group}."
    MULTIPLE_GROUPS_MSG = "User could review more than one group: {groups}"

    def __init__(self, remote, user, request_id):
        super(AssignAction, self).__init__(remote, user)
        self.request = Request.by_id(self.remote, request_id)

    def action(self, group_to_replace=None):
        if group_to_replace:
            self.assign(group_to_replace)
        else:
            group = self.infer_group()
            # TODO: Ensure that the user actually wants this?
            self.assign(group)

    def infer_group(self):
        """Based on the given user and request id search for a group that
        the user could do the review for.

        """
        user_groups = set(self.user.qam_groups)
        reviews = [review for review in self.request.review_list() if
                   review.review_type == Request.REVIEW_GROUP]
        open_groups = set([Group.for_name(self.remote, review.name) for review
                           in reviews])
        both = user_groups.intersection(open_groups)
        if not both:
            err = "No matching qam-groups found for user: {u}".format(
                u=self.user
            )
            raise UninferableError(err)
        else:
            if len(both) > 1:
                error = AssignAction.MULTIPLE_GROUPS_MSG.format(group=both)
                raise UninferableError(error)
            else:
                group = both.pop()
                msg = AssignAction.AUTO_INFER_MSG.format(group=group)
                print(msg)
                return group

    def assign(self, group):
        msg = AssignAction.ASSIGN_USER_MSG.format(
            user=self.user, group=group, request=self.request
        )
        print(msg)
        self.request.review_add(user=self.user)
        self.undo_stack.append(
            lambda: self.request.review_accept(user=self.user)
        )
        self.request.review_accept(group=group)
        self.undo_stack.append(
            lambda: self.request.review_reopen(group=group)
        )


class UnassignAction(OscAction):
    """Will unassign the user from the review and reopen the request for
    the group the user assign himself for.
    """
    GROUP_NOT_INFERRED_MSG = "Can not auto-detect which group is affected."
    UNASSIGN_USER_MSG = "Will unassign {user} from {request} for group {group}"

    def __init__(self, remote, user, request_id):
        super(UnassignAction, self).__init__(remote, user)
        self.request = Request.by_id(self.remote, request_id)

    def action(self):
        group_to_readd = self.infer_group()
        if not group_to_readd or len(group_to_readd) > 1:
            raise UninferableError(UnassignAction.GROUP_NOT_INFERRED_MSG)
        group_to_readd = Group.for_name(self.remote, group_to_readd[0])
        self.unassign(group_to_readd)

    def infer_group(self):
        """Search for the group the given user started a review for.

        """
        # TODO: This should be extended to take into account reviews that
        # might be done by > 1 person, which requires:
        # 1) Storing the history of a review.
        # 2) Checking in history which group was accepted.
        group_reviews = [r for r in self.request.reviews
                         if r.by_group != None]
        reviews_for_user_group = []
        for group_review in group_reviews:
            if group_review.state == 'accepted':
                if group_review.who == self.user.login:
                    reviews_for_user_group.append(group_review.by_group)
        return reviews_for_user_group

    def unassign(self, group):
        msg = UnassignAction.UNASSIGN_USER_MSG.format(
            user=self.user, group=group, request=self.request
        )
        print(msg)
        self.request.review_reopen(group=group)
        self.undo_stack.append(
            lambda: self.request.review_accept(group=group,
                                               comment='Reverting due to error.')
        )
        self.request.review_accept(user=self.user)
        self.undo_stack.append(
            lambda: self.request.review_reopen(user=self.user,
                                               comment='Reverting due to error.')
        )


class ApproveAction(OscAction):
    """Approve a review for a user and group.
    
    Attempts to automatically find the group that the user assigned himself
    for and will approve that group if possible.

    """
    APPROVE_MSG = "Will approve {request} for {user}."
    
    def __init__(self, remote, user, request_id):
        super(ApproveAction, self).__init__(remote, user)
        self.request = Request.by_id(self.remote, request_id)
    
    def action(self):
        msg = ApproveAction.APPROVE_MSG.format(user=self.user,
                                               request=self.request)
        print(msg)
        self.request.review_accept(user=self.user)


class RejectAction(OscAction):
    """Reject a request for a user and group.
    
    Attempts to automatically find the group that the user assigned himself
    for and will reject that group if possible.

    """
    DECLINE_MSG = "Will decline {request} for {user}."
    
    def __init__(self, remote, user, request_id):
        super(RejectAction, self).__init__(remote, user)
        self.request = Request.by_id(self.remote, request_id)
        self._template = None

    @property
    def template(self):
        if not self._template:
            self._template = Template.for_request(self.request)
        return self._template
    
    def action(self, comment=None):
        comment = self.get_failure()
        msg = RejectAction.DECLINE_MSG.format(user=self.user,
                                               request=self.request)
        print(msg)
        self.request.review_decline(user=self.user)

    def get_failure(self):
        """Get the failure message from the template.

        If the template says the test did not fail this will raise en error.

        """
        status = self.template.status
        if status != Template.STATUS_FAILURE:
            msg = "Request-Status not 'FAILED': please check report: {p}".format(
                p=self.template.directory
            )
            raise ActionError(msg)
        return self.template.log_entries['comment']


class CommentAction(OscAction):
    """Add a comment to a review.
    
    """
    def __init__(self, remote, user, request_id, comment):
        super(CommentAction, self).__init__(remote, user)
        self.comment = comment
        self.request = Request.by_id(self.remote, request_id)

    def action(self):
        self.request.add_comment(comment, user=self.user)
