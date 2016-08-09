from __future__ import print_function
import abc
import os
import itertools
import logging
import multiprocessing
import re
import sys

from concurrent.futures import ThreadPoolExecutor, as_completed
import osc.conf

from .errors import (NoCommentError,
                     NonMatchingGroupsError,
                     NonMatchingUserGroupsError,
                     NotAssignedError,
                     NotPreviousReviewerError,
                     NoReviewError,
                     ReportedError,
                     ReportNotYetGeneratedError,
                     TemplateNotFoundError,
                     UninferableError)
from .models import (Group, GroupReview, User, Request, Template,
                     UserReview)
from .remotes import RemoteError
from .fields import ReportField

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PREFIX = "[oscqam]"


def get_number_of_threads():
    """Return the number of threads to use when retrieving templates in parallel.

    Will either use a configured value in 'oscqam_max_threads' from ~/.oscrc
    or default to the number of CPUs.

    """
    osc.conf.get_config()
    return osc.conf.config.get('oscqam_max_threads',
                               multiprocessing.cpu_count())


def multi_level_sort(xs, criteria):
    """Sort the given collection based on multiple criteria.
    The criteria will be sorted by in the given order, whereas each group
    from the first criteria will be sorted by the second criteria and so forth.

    :param xs: Iterable of objects.
    :type xs: [a]

    :param criteria: Iterable of extractor functions.
    :type criteria: [a -> b]

    """
    if not criteria:
        return xs
    extractor = criteria[-1]
    xss = sorted(xs, key = extractor)
    grouped = itertools.groupby(xss, extractor)
    subsorts = [multi_level_sort(list(value), criteria[:-1]) for _, value in
                grouped]
    return [s for sub in subsorts for s in sub]


class OscAction(object):
    """Base class for actions that need to interface with the open build service.

    """
    def __init__(self, remote, user, out = sys.stdout):
        """
        :param remote: Remote endpoint to the buildservice.
        :type remote: :class:`oscqam.models.RemoteFacade`

        :param user: Username that performs the action.
        :type user: str

        :param out: Filelike to print enduser-messages to.
        :type out: :class:`file`
        """
        self.remote = remote
        self.user = remote.users.by_name(user)
        self.undo_stack = []
        self.out = out

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

    def print(self, msg, end = os.linesep):
        """Mimick the print-statements behaviour on the out-stream:

        Print the given message and add a newline.

        :type msg: str
        """
        self.out.write(msg)
        self.out.write(end)
        self.out.flush()


class Report(object):
    """Composes request with the matching template.

    Provides a method to output a list of keys from requests/templates and
    will dispatch to the correct object.

    """

    def __init__(self, request, template_factory):
        """Associate a request with the correct template."""
        self.request = request
        self.template = request.get_template(template_factory)

    def value(self, field):
        """Return the values for fields.

        :type keys: [:class:`actions.ReportField`]
        :param keys: Identifiers for the data to be returned from the template
                    or associated request.

        :returns: [str]
        """
        entries = self.template.log_entries
        if field == ReportField.unassigned_roles:
            reviews = [review for review
                       in self.request.review_list_open()
                       if isinstance(review, GroupReview)]
            value = sorted([str(r.reviewer) for r in reviews])
        elif field == ReportField.package_streams:
            value = [p for p in self.request.packages]
        elif field == ReportField.assigned_roles:
            roles = self.request.assigned_roles
            value = [str(r) for r in roles]
        elif field == ReportField.incident_priority:
            value = self.request.incident_priority
        elif field == ReportField.comments:
            value = self.request.comments
        elif field == ReportField.creator:
            value = self.request.creator
        else:
            value = entries[str(field)]
        return value


class ListAction(OscAction):
    """Base action for operation that work on a list of requests.

    Subclasses must overwrite the 'load_requests' method that return the list
    of requests that should be output according to the formatter and fields.
    """
    __metaclass__ = abc.ABCMeta
    default_fields = [ReportField.review_request_id,
                      ReportField.srcrpms,
                      ReportField.rating,
                      ReportField.products,
                      ReportField.incident_priority]

    def group_sort_reports(self):
        """Sort reports according to rating and request id.

        First sort by Priority, then rating and finally request id.
        """
        reports = filter(None, self.reports)
        self.reports = multi_level_sort(
            reports,
            [lambda l: l.request.reqid,
             lambda l: l.template.log_entries["Rating"],
             lambda l: l.request.incident_priority]
        )

    def __init__(self, remote, user, template_factory = Template):
        super(ListAction, self).__init__(remote, user)
        self.template_factory = template_factory

    def action(self):
        """Return all reviews that match the parameters of the RequestAction.

        """
        self.reports = self._load_listdata(self.load_requests())
        self.group_sort_reports()
        return self.reports

    @abc.abstractmethod
    def load_requests(self):
        """Load requests this class should operate on.

        :returns: [:class:`oscqam.models.Request`]
        """
        pass

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

    def _load_listdata(self, requests):
        """Load templates for the given requests.

        Templates that could not be loaded will print a warning (this can
        occur and not be a problem: e.g. the template creation script has not
        yet run).

        :param requests: [:class:`oscqam.models.Request`]

        :returns: :class:`oscqam.actions.Report`-generator
        """
        with ThreadPoolExecutor(max_workers = get_number_of_threads()) as executor:
            results = [executor.submit(Report, r, self.template_factory)
                       for r in requests]
        for promise in as_completed(results):
            try:
                yield promise.result()
            except TemplateNotFoundError as e:
                logger.warning(str(e))


class ListOpenAction(ListAction):
    def load_requests(self):
        def assigned(req):
            """Check if the request is assigned to the user that requests the
            listing."""
            for review in req.assigned_roles:
                if review.reviewer == self.user:
                    return True
            return False

        user_requests = set(self.remote.requests.for_user(self.user))
        filters = lambda req: req.active() and assigned(req)
        user_requests = set(filter(filters, user_requests))
        qam_groups = self.user.qam_groups
        if not qam_groups:
            raise ReportedError("You are not part of a qam group. "
                                "Can not list requests.")
        group_requests = set(self.remote.requests.open_for_groups(qam_groups))
        return self.merge_requests(user_requests, group_requests)


class ListGroupAction(ListAction):
    def __init__(self, remote, user, groups, template_factory = Template):
        super(ListGroupAction, self).__init__(remote, user,
                                              template_factory)
        if not groups:
            raise AttributeError("Can not list groups without any groups.")
        self.groups = [self.remote.groups.for_name(group) for group in groups]

    def load_requests(self):
        return set(self.remote.requests.open_for_groups(self.groups))


class ListAssignedAction(ListAction):
    """Action to list assigned requests.
    """
    default_fields = [ReportField.review_request_id,
                      ReportField.srcrpms,
                      ReportField.rating,
                      ReportField.products,
                      ReportField.incident_priority,
                      ReportField.assigned_roles,
                      ReportField.creator]

    def in_review_by_user(self, reviews):
        for review in reviews:
            if (review.reviewer == self.user and review.open):
                return True
        return False

    def load_requests(self):
        qam_groups = [group for group in self.remote.groups.all()
                      if group.is_qam_group()]
        return set([request for request in
                    self.remote.requests.review_for_groups(qam_groups)])


class ListAssignedGroupAction(ListAssignedAction):
    def __init__(self, remote, user, groups, template_factory = Template):
        super(ListAssignedGroupAction, self).__init__(remote, user,
                                                      template_factory)
        if not groups:
            raise AttributeError("Can not list groups without any groups.")
        self.groups = [self.remote.groups.for_name(group) for group in groups]

    def in_review(self, reviews):
        for review in reviews:
            if review.reviewer in self.groups:
                return True
        return False

    def load_requests(self):
        group_requests = set(self.remote.requests.review_for_groups(
            self.groups
        ))
        return set([request for request in group_requests
                    if self.in_review(request.review_list())])


class ListAssignedUserAction(ListAssignedAction):
    """Action to list requests that are assigned to the user.
    """
    def load_requests(self):
        user_requests = set(self.remote.requests.for_user(self.user))
        return set([request for request in user_requests
                    if self.in_review_by_user(request.review_list())])


class InfoAction(ListAction):
    default_fields = [ReportField.review_request_id,
                      ReportField.srcrpms,
                      ReportField.rating,
                      ReportField.products,
                      ReportField.incident_priority,
                      ReportField.assigned_roles,
                      ReportField.unassigned_roles,
                      ReportField.creator]

    def __init__(self, remote, user_id, request_id):
        super(InfoAction, self).__init__(remote, user_id)
        self.request = remote.requests.by_id(request_id)

    def load_requests(self):
        return [self.request]


class AssignAction(OscAction):
    ASSIGN_MSG = "Assigning {user} to {group} for {request}."
    AUTO_INFER_MSG = "Found a possible group: {group}."
    MULTIPLE_GROUPS_MSG = "User could review more than one group: {groups}"

    def __init__(self, remote, user, request_id, groups = None,
                 template_factory = Template, force = False,
                 template_required = True, **kwargs):
        super(AssignAction, self).__init__(remote, user, **kwargs)
        self.request = remote.requests.by_id(request_id)
        if groups:
            self.groups = [remote.groups.for_name(group) for group in groups]
        else:
            self.groups = None
        self.template_factory = template_factory
        self.template_required = template_required
        self.force = force

    def template_exists(self):
        """Check that the template associated with the request exists.

        If the template is not yet generated, assigning a user can lead
        to the template-generator no longer finding the request and
        never generating the template.
        """
        try:
            self.request.get_template(self.template_factory)
        except TemplateNotFoundError:
            raise ReportNotYetGeneratedError(self.request)

    def check_previous_rejects(self):
        """If there were previous rejects for an incident users that have
        already reviewed this incident should (preferably) review it again.

        If the user trying to assign himself is not one of the previous
        reviewers a warning is issued.
        """
        related_requests = self.remote.requests.for_incident(
            self.request.src_project
        )
        if not related_requests:
            return
        declined_requests = [request for request in related_requests
                             if request.state.name == Request.STATE_DECLINED]
        if not declined_requests:
            return
        reviewers = [review.reviewer for review in request.review_list()
                     for request in declined_requests
                     if isinstance(review, UserReview)]
        if self.user not in reviewers:
            raise NotPreviousReviewerError(reviewers)

    def validate(self):
        if self.force:
            return
        if self.template_required:
            self.template_exists()
        self.check_previous_rejects()

    def action(self):
        if self.groups:
            self.assign(self.groups)
        else:
            group = self.reviewable_group()
            # TODO: Ensure that the user actually wants this?
            self.assign(group)

    def reviewable_group(self):
        """Based on the given user and request search for a group that
        the user could do the review for.

        """
        groups = self.user.reviewable_groups(self.request)
        if len(groups) > 1:
            raise UninferableError(
                AssignAction.MULTIPLE_GROUPS_MSG.format(
                    groups = [str(g) for g in groups]
                )
            )
        group = groups.pop()
        self.print(AssignAction.AUTO_INFER_MSG.format(group = group))
        return [group]

    def assign(self, groups):
        self.validate()
        for group in groups:
            msg = AssignAction.ASSIGN_MSG.format(
                user = self.user, group = group, request = self.request
            )
            self.request.review_assign(reviewer = self.user,
                                       group = group,
                                       comment = msg)
            self.print(msg)


class UnassignAction(OscAction):
    """Will unassign the user from the review and reopen the request for
    the group the user assign himself for.
    """
    UNASSIGN_MSG = "Unassigning {user} from {request} for group {group}."
    ACCEPT_USER_MSG = "Will close review for {user}"

    def __init__(self, remote, user, request_id, groups = None, **kwargs):
        super(UnassignAction, self).__init__(remote, user, **kwargs)
        self.request = remote.requests.by_id(request_id)
        if groups:
            self._groups = [remote.groups.for_name(group) for group in groups]
        else:
            self._groups = None

    def groups(self):
        if self._groups:
            return self._groups
        return self.review_groups()

    def action(self):
        assigned_groups = self.review_groups()
        self.unassign(self.groups(), assigned_groups)

    def review_groups(self):
        """Find the exact group the user is currently reviewing and return it.

        :return: Group in review by the user.
        :raise NoReviewError: If the user is not reviewing any group of the
            request.
        :raise MultipleReviewsError: If more than one group is assigned to
            the user.

        """
        groups = self.user.in_review_groups(self.request)
        if not groups:
            raise NoReviewError(self.user)
        return groups

    def undo_reopen(self, group, comment):
        def _():
            self.print("UNDO: Undoing reopening of group {group}".format(
                group = group
            ))
            self.request.review_accept(group = group,
                                       comment = comment)
        return _

    def undo_accept(self, user):
        def _():
            self.print("UNDO: Undoing accepting user {user}".format(
                user = user
            ))
            self.request.review_reopen(user = self.user)
        return _

    def unassign(self, groups, assigned_groups):
        difference = set(assigned_groups).difference(set(groups))
        for group in groups:
            msg = UnassignAction.UNASSIGN_MSG.format(
                user = self.user, group = group, request = self.request
            )
            self.print(msg)
            undo_comment = AssignAction.ASSIGN_MSG.format(
                user = self.user, group = group, request = self.request
            )
            self.request.review_reopen(group = group,
                                       comment = msg)
            self.undo_stack.append(
                self.undo_reopen(group, undo_comment)
            )
        if not difference:
            msg = UnassignAction.ACCEPT_USER_MSG.format(
                user = self.user, request = self.request
            )
            comment = UnassignAction.UNASSIGN_MSG.format(
                user = self.user,
                request = self.request,
                group = ', '.join(sorted([str(g) for g in groups]))
            )
            self.print(msg)
            self.request.review_accept(user = self.user, comment = comment)
            self.undo_stack.append(
                self.undo_accept(self.user)
            )


class ApproveAction(OscAction):
    """Template class for Approval actions.

    Subclasses need to overwrite:

    - get_reviewer: whose review is done.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, remote, user, request_id, reviewer,
                 template_factory = Template, out = sys.stdout):
        """Approve a review for either a User or a Group.

        :param remote: Remote interface for build service calls.
        :type remote: L{oscqam.remote.RemoteFacade}

        :param user: The user performing this action.
        :type user: L{string}

        :param request_id: Id of the request to accept.
        :type request_id: L{int}

        :param reviewer: Reviewer to accept this request for.
        :type reviewer: L{oscqam.models.User} | L{oscqam.models.Group}

        :param template_factory: Function to get a report-template from.
        :type template_factory:

        :param out: File like object to write output messages to.
        :type out:
        """
        super(ApproveAction, self).__init__(remote, user, out)
        self.request = remote.requests.by_id(request_id)
        self.template = self.request.get_template(template_factory)
        self.reviewer = self.get_reviewer(reviewer)

    @abc.abstractmethod
    def get_reviewer(self, reviwer):
        """Return the object for the given reviewer."""
        pass


class ApproveUserAction(ApproveAction):
    """Approve a review for a user.

    """
    APPROVE_MSG = ("Approving {request} for {user} ({groups}). "
                   "Testreport: {url}")
    MORE_GROUPS_MSG = ("The following groups could also be reviewed by you: "
                       "{groups}")

    def get_reviewer(self, reviewer):
        return self.remote.users.by_name(reviewer)

    def reviews_assigned(self):
        """Ensure that the user was assigned before accepting."""
        for review in self.request.assigned_roles:
            if review.user == self.user:
                return True
        else:
            raise NotAssignedError(self.user)

    def validate(self):
        """Check preconditions to be met before a request can be approved.

        :raises: :class:`oscqam.models.TestResultMismatchError` or
        :class:`oscqam.models.TestPlanReviewerNotSetError` if conditions
        are not met.

        """
        self.reviews_assigned()
        self.template.testplanreviewer()
        self.template.passed()

    def additional_reviews(self):
        """Return groups that could also be reviewed by the user."""
        return self.user.reviewable_groups(self.request)

    def action(self):
        self.validate()
        url = self.template.url()
        groups = ", ".join([str(g) for g in self.user.in_review_groups(self.request)])
        msg = self.APPROVE_MSG.format(user = self.reviewer,
                                      groups = groups,
                                      request = self.request,
                                      url = url)
        self.print(msg)
        self.request.review_accept(user = self.reviewer,
                                   comment = msg)
        try:
            groups = ', '.join([str(g) for g in self.additional_reviews()])
            msg = self.MORE_GROUPS_MSG.format(groups = groups)
            self.print(msg)
        except NonMatchingUserGroupsError:
            pass


class ApproveGroupAction(ApproveAction):
    APPROVE_MSG = "Approving {request} for group {group}."

    def get_reviewer(self, reviewer):
        return self.remote.groups.for_name(reviewer)

    def validate(self):
        if self.reviewer not in self.request.groups:
            raise NonMatchingGroupsError([self.reviewer], self.request.groups)

    def action(self):
        self.validate()
        msg = self.APPROVE_MSG.format(request = self.request,
                                      group = self.reviewer)
        self.print(msg)
        self.request.review_accept(group = self.reviewer,
                                   comment = msg)


class RejectAction(OscAction):
    """Reject a request for a user and group.

    Attempts to automatically find the group that the user assigned himself
    for and will reject that group if possible.

    """
    DECLINE_MSG = "Declining request {request} for {user}. See Testreport: {url}"

    def __init__(self, remote, user, request_id, reason, message = None,
                 out = sys.stdout):
        super(RejectAction, self).__init__(remote, user, out = out)
        self.request = remote.requests.by_id(request_id)
        self._template = None
        self.reason = reason
        self.message = message

    @property
    def template(self):
        if not self._template:
            self._template = Template(self.request)
        return self._template

    def validate(self):
        """Check preconditions to be met before a request can be approved.

        :raises: :class:`oscqam.models.TestResultMismatchError` or
            :class:`oscqam.models.TestPlanReviewerNotSetError` if conditions
            are not met.

        """
        self.template.failed()
        if not self.template.log_entries['comment']:
            raise NoCommentError()

    def action(self):
        self.validate()
        comment = self.template.log_entries['comment']
        if self.message:
            comment = self.message
        url = self.template.url()
        msg = RejectAction.DECLINE_MSG.format(user = self.user,
                                              request = self.request,
                                              url = url)
        self.print(msg)
        self.request.review_decline(user = self.user,
                                    comment = msg,
                                    reasons = self.reason)


class CommentAction(OscAction):
    """Add a comment to a request.

    """
    def __init__(self, remote, user, request_id, comment):
        super(CommentAction, self).__init__(remote, user)
        self.comment = comment
        self.request = remote.requests.by_id(request_id)

    def action(self):
        self.request.add_comment(self.comment)


class DeleteCommentAction(OscAction):
    """Delete a comment.
    """
    def __init__(self, remote, user, comment_id):
        super(DeleteCommentAction, self).__init__(remote, user)
        self.comment_id = comment_id

    def action(self):
        self.remote.comments.delete(self.comment_id)
