from __future__ import print_function
import logging
from .models import (Group, User, Request, Template, ReportedError,
                     RemoteError, TemplateNotFoundError)
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PREFIX = "[oscqam]"


class ActionError(ReportedError):
    """General error to raise when an error occurred while performing one of the
    actions.

    """


class UninferableError(ReportedError, ValueError):
    """Error to raise when the program should try to auto-infer some values, but
    can not do so due to ambiguity.

    """


class NoQamReviewsError(UninferableError):
    """Error when no qam groups still need a review.

    """
    def __init__(self, accepted_reviews):
        """Create new error for accepted reviews.
        """
        message = "No 'qam'-groups need review."
        accept_reviews = [review for review
                          in accepted_reviews
                          if review.review_type == Request.REVIEW_GROUP]
        message += (" The following groups were already accepted: "
                    "{msg}".format(
                        msg=", ".join(["{r.by_group} (by {r.who})".format(r=review)
                                       for review in accept_reviews])
                    )) if accept_reviews else ""
        super(NoQamReviewsError, self).__init__(message)


class NonMatchingGroupsError(UninferableError):
    """Error when the user is not a member of a group that still needs to review
    the request.

    """
    _msg = ("User groups and required groups don't match: "
            "User-groups: {ug}, required-groups: {og}.")

    def __init__(self, user, user_groups, open_groups):
        message = (self._msg.format(
            user=user,
            ug=[g.name for g in user_groups],
            og=[r.name for r in open_groups],
        ))
        super(NonMatchingGroupsError, self).__init__(message)


class NoReviewError(UninferableError):
    """Error to raise when a user attempts an unassign action for a request he did
    not start a review for.

    """
    def __init__(self, user):
        super(NoReviewError, self).__init__(
            "User {u} is not assigned for any groups.".format(
                u=user
            )
        )


class MultipleReviewsError(UninferableError):
    """Error to raise when a user attempts an unassign action for a request he is
    reviewing for multiple groups at once.

    """
    def __init__(self, user, groups):
        super(MultipleReviewsError, self).__init__(
            "User {u} is currently reviewing for mulitple groups: {g}."
            "Please provide which group to unassign via -G parameter.".format(
                u=user,
                g=groups
            )
        )


class TestResultMismatchError(ReportedError):
    _msg = "Request-Status not '{0}': please check report: {1}"

    def __init__(self, expected, log_path):
        super(TestResultMismatchError, self).__init__(
            self._msg.format(expected, log_path)
        )


class OscAction(object):
    """Base class for actions that need to interface with the open build service.

    """
    def __init__(self, remote, user):
        self.remote = remote
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
    class ListData(object):
        def __init__(self, request, template_factory):
            """Associate a request with the correct template."""
            self.request = request
            self.template = request.get_template(template_factory)

        def values(self, keys):
            """Return the values for keys.

            :type keys: [str]
            :param keys: Identifiers for the data to be returned from the template
                        or associated request.

            :returns: [str]
            """
            data = []
            entries = self.template.log_entries
            for key in keys:
                try:
                    if key == "Unassigned Roles":
                        names = [r.name for r in self.request.review_list_open()]
                        value = " ".join(names)
                    elif key == "Package-Streams":
                        packages = [p for p in self.request.packages]
                        value = " ".join(packages)
                    elif key == "Assigned Roles":
                        roles = self.request.assigned_roles
                        assigns = ["{r.user} ({r.group})".format(r = r)
                                for r in roles]
                        value = ", ".join(assigns)
                    elif key == "Incident Priority":
                        value = self.request.incident_priority
                    else:
                        value = entries[key]
                    data.append(value)
                except KeyError:
                    logger.debug("Missing key: %s", key)
            return data

    def __init__(self, remote, user, only_review=False):
        super(ListAction, self).__init__(remote, user)
        self.only_review = only_review

    def merge_requests(self, user_requests, group_requests):
        """Merge the requests together and set a field 'origin' to determine
        where the request came from.

        """
        all_requests = user_requests.union(group_requests)
        for request in all_requests:
            request.origin = []
            if request in user_requests:
                request.origin.append(self.user.login)
            if request in group_requests:
                request.origin.extend(request.groups)
        return all_requests

    def in_review_by_user(self, reviews):
        for review in reviews:
            if (review.by_user == self.user.login
                    and review.state == 'new'):
                return True
        return False

    def action(self):
        """Return all reviews that match the parameters of the RequestAction.

        """
        user_requests = set(Request.for_user(self.remote, self.user))
        if self.only_review:
            all_requests = set([request for request in user_requests
                                if self.in_review_by_user(request.review_list())])
            all_requests = self.merge_requests(all_requests, [])
        else:
            qam_groups = self.user.qam_groups
            group_requests = set(Request.open_for_groups(self.remote,
                                                         qam_groups))
            all_requests = self.merge_requests(user_requests, group_requests)
        return self._load_listdata(all_requests)

    def _load_listdata(self, requests):
        """Load templates for the given requests.

        Templates that could not be loaded will print a warning (this can
        occur and not be a problem: e.g. the template creation script has not
        yet run).

        :param requests: [L{oscqam.models.Request}]

        :returns: [L{oscqam.actions.ListAction.ListData}]
        """
        listdata = []
        for request in requests:
            try:
                listdata.append(self.ListData(request,
                                              self.template_factory))
            except TemplateNotFoundError as e:
                logger.warning(str(e))
        return listdata


class AssignAction(OscAction):
    ASSIGN_COMMENT = "{prefix}::assign::{user.login}::{group.name}"
    ASSIGN_USER_MSG = ("Will assign {user} to {group} for {request}.")
    AUTO_INFER_MSG = "Found a possible group: {group}."
    MULTIPLE_GROUPS_MSG = "User could review more than one group: {groups}"

    def __init__(self, remote, user, request_id, group=None):
        super(AssignAction, self).__init__(remote, user)
        self.request = Request.by_id(self.remote, request_id)
        self.group = group

    def action(self):
        if self.group:
            self.assign(self.group)
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
                   (review.review_type == Request.REVIEW_GROUP and
                    review.state.lower() == 'new')]
        review_groups = [Group.for_name(self.remote, review.name) for review
                         in reviews]
        open_groups = set(review_groups)
        if not open_groups:
            raise NoQamReviewsError(self.request.review_list_accepted())
        both = user_groups.intersection(open_groups)
        if not both:
            raise NonMatchingGroupsError(self.user, user_groups, open_groups)
        if len(both) > 1:
            raise UninferableError(
                AssignAction.MULTIPLE_GROUPS_MSG.format(group=both)
            )
        group = both.pop()
        print(AssignAction.AUTO_INFER_MSG.format(group=group))
        return group

    def assign(self, group):
        msg = AssignAction.ASSIGN_USER_MSG.format(
            user=self.user, group=group, request=self.request
        )
        print(msg)
        comment = AssignAction.ASSIGN_COMMENT.format(
            prefix=PREFIX, user=self.user, group=group
        )
        self.request.review_assign(reviewer=self.user,
                                   group=group,
                                   comment=comment)


class UnassignAction(OscAction):
    """Will unassign the user from the review and reopen the request for
    the group the user assign himself for.
    """
    UNASSIGN_COMMENT = "{prefix}::unassign::{user.login}::{group.name}"
    UNASSIGN_USER_MSG = "Will unassign {user} from {request} for group {group}"

    def __init__(self, remote, user, request_id, group=None):
        super(UnassignAction, self).__init__(remote, user)
        self.request = Request.by_id(self.remote, request_id)
        self._group = Group.for_name(self.remote, group) if group else None

    def group(self):
        if self._group:
            return self._group
        return self.infer_group()

    def action(self):
        self.unassign(self.group())

    def possible_groups(self):
        """Will return all groups the user assigned himself for and is
        currently in the state of doing a review.
        """
        possible_groups = []
        for role in self.request.assigned_roles:
            if role.user == self.user:
                possible_groups.append(role.group)
        return possible_groups

    def infer_group(self):
        """Find the exact group the user is currently reviewing and return it.

        :return: Group in review by the user.
        :raise NoReviewError: If the user is not reviewing any group of the
            request.
        :raise MultipleReviewsError: If more than one group is assigned to
            the user.

        """
        groups = self.possible_groups()
        if not groups:
            raise NoReviewError(self.user)
        elif len(groups) > 1:
            raise MultipleReviewsError(self.user, groups)
        return groups.pop()

    def unassign(self, group):
        msg = UnassignAction.UNASSIGN_USER_MSG.format(
            user=self.user, group=group, request=self.request
        )
        print(msg)
        comment = UnassignAction.UNASSIGN_COMMENT.format(
            prefix=PREFIX, user=self.user, group=group
        )
        undo_comment = AssignAction.ASSIGN_COMMENT.format(
            prefix=PREFIX, user=self.user, group=group
        )
        self.request.review_reopen(group=group,
                                   comment=comment)
        self.undo_stack.append(
            lambda: self.request.review_accept(group=group,
                                               comment=undo_comment)
        )
        self.request.review_accept(user=self.user, comment=comment)
        self.undo_stack.append(
            lambda: self.request.review_reopen(user=self.user)
        )


class ApproveAction(OscAction):
    """Approve a review for a user.

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

    def __init__(self, remote, user, request_id, message=None):
        super(RejectAction, self).__init__(remote, user)
        self.request = Request.by_id(self.remote, request_id)
        self._template = None
        self.message = message

    @property
    def template(self):
        if not self._template:
            self._template = Template(self.request)
        return self._template

    def action(self):
        comment = self.get_failure()
        if self.message or not comment:
            comment = self.message
        msg = RejectAction.DECLINE_MSG.format(user=self.user,
                                              request=self.request)
        print(msg)
        if not comment:
            raise ActionError("Must provide a message for reject.")
        self.request.review_decline(user=self.user, comment=comment)

    def get_failure(self):
        """Get the failure message from the template.

        If the template says the test did not fail this will raise an error.

        """
        status = self.template.status
        if status != Template.STATUS_FAILURE:
            raise TestResultMismatchError(
                'FAILED',
                self.template.log_path
            )
        return self.template.log_entries['comment']


class CommentAction(OscAction):
    """Add a comment to a request.

    """
    def __init__(self, remote, user, request_id, comment):
        super(CommentAction, self).__init__(remote, user)
        self.comment = comment
        self.request = Request.by_id(self.remote, request_id)

    def action(self):
        self.request.add_comment(self.comment)
