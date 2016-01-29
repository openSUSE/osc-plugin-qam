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

from .models import (Group, GroupReview, User, Request, Template,
                     ReportedError, TemplateNotFoundError, UserReview)
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
                          if isinstance(review, GroupReview)]
        message += (" The following groups were already assigned/finished: "
                    "{msg}".format(
                        msg = ", ".join(["{r.reviewer}".format(
                            r = review
                        ) for review in accept_reviews])
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
            user = user,
            ug = [g.name for g in user_groups],
            og = [r.name for r in open_groups],
        ))
        super(NonMatchingGroupsError, self).__init__(message)


class NoReviewError(UninferableError):
    """Error to raise when a user attempts an unassign action for a request he did
    not start a review for.

    """
    def __init__(self, user):
        super(NoReviewError, self).__init__(
            "User {u} is not assigned for any groups.".format(
                u = user
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
                u = user,
                g = groups
            )
        )


class ReportNotYetGeneratedError(ReportedError):
    _msg = ("The report for request '{0}' is not generated yet. "
            "To prevent bugs in the template parser, assigning "
            "is not yet possible.")

    def __init__(self, request):
        super(ReportNotYetGeneratedError, self).__init__(
            self._msg.format(str(request))
        )


class OneGroupAssignedError(ReportedError):
    _msg = ("User {user} is already assigned for group {group}. "
            "Assigning for multiple groups at once is currently not allowed "
            "to prevent inconsistent states in the build service.")

    def __init__(self, assignment):
        super(OneGroupAssignedError, self).__init__(
            self._msg.format(user = str(assignment.user),
                             group = str(assignment.group))
        )


class NotPreviousReviewerError(ReportedError):
    _msg = ("This request was previously rejected and you were not part "
            "of the previous set of reviewers: {reviewers}.")

    def __init__(self, reviewers):
        super(NotPreviousReviewerError, self).__init__(
            self._msg.format(reviewers = reviewers)
        )


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
            names = sorted([str(r.reviewer) for r in reviews])
            value = " ".join(names)
        elif field == ReportField.package_streams:
            packages = [p for p in self.request.packages]
            value = " ".join(packages)
        elif field == ReportField.assigned_roles:
            roles = self.request.assigned_roles
            value = [str(r) for r in roles]
        elif field == ReportField.incident_priority:
            value = self.request.incident_priority
        elif field == ReportField.comments:
            value = self.request.comments
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


class ListAssignedAction(ListAction):
    """Action to list assigned requests.
    """
    default_fields = [ReportField.review_request_id,
                      ReportField.srcrpms,
                      ReportField.rating,
                      ReportField.products,
                      ReportField.incident_priority,
                      ReportField.assigned_roles]

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
                      ReportField.unassigned_roles]

    def __init__(self, remote, user_id, request_id):
        super(InfoAction, self).__init__(remote, user_id)
        self.request = remote.requests.by_id(request_id)

    def load_requests(self):
        return [self.request]


class AssignAction(OscAction):
    ASSIGN_COMMENT = "{prefix}::assign::{user.login}::{group.name}"
    ASSIGN_USER_MSG = ("Assigned {user} to {group} for {request}.")
    AUTO_INFER_MSG = "Found a possible group: {group}."
    MULTIPLE_GROUPS_MSG = "User could review more than one group: {groups}"

    def __init__(self, remote, user, request_id, group = None,
                 template_factory = Template, force = False,
                 template_required = True, **kwargs):
        super(AssignAction, self).__init__(remote, user, **kwargs)
        self.request = remote.requests.by_id(request_id)
        self.group = remote.groups.for_name(group) if group else None
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

    def first_group_assigned(self):
        """Prevent a user from assigned more than 1 group at a time.

        The buildservice creates only one user review, even if the user
        assigns to 2 groups.
        This user-review will be closed as soon as the user accepts the
        first review, leading to inconsistent state in the buildservice.

        Not allowing a user to assign for > 1 group at a time at least
        prevents this.
        """
        for assignment in self.request.assigned_roles:
            if assignment.user == self.user:
                raise OneGroupAssignedError(assignment)

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
        self.first_group_assigned()
        self.check_previous_rejects()

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
                   (isinstance(review, GroupReview) and review.open
                    and review.reviewer.is_qam_group())]
        review_groups = [review.reviewer for review in reviews]
        open_groups = set(review_groups)
        if not open_groups:
            raise NoQamReviewsError(self.request.review_list_accepted())
        both = user_groups.intersection(open_groups)
        if not both:
            raise NonMatchingGroupsError(self.user, user_groups, open_groups)
        if len(both) > 1:
            raise UninferableError(
                AssignAction.MULTIPLE_GROUPS_MSG.format(
                    groups = [str(g) for g in both]
                )
            )
        group = both.pop()
        print(AssignAction.AUTO_INFER_MSG.format(group = group))
        return group

    def assign(self, group):
        self.validate()
        msg = AssignAction.ASSIGN_USER_MSG.format(
            user = self.user, group = group, request = self.request
        )
        comment = AssignAction.ASSIGN_COMMENT.format(
            prefix = PREFIX, user = self.user, group = group
        )
        self.request.review_assign(reviewer = self.user,
                                   group = group,
                                   comment = comment)
        self.print(msg)


class UnassignAction(OscAction):
    """Will unassign the user from the review and reopen the request for
    the group the user assign himself for.
    """
    UNASSIGN_COMMENT = "{prefix}::unassign::{user.login}::{group.name}"
    UNASSIGN_USER_MSG = "Will unassign {user} from {request} for group {group}"

    def __init__(self, remote, user, request_id, group = None):
        super(UnassignAction, self).__init__(remote, user)
        self.request = remote.requests.by_id(request_id)
        self._group = remote.groups.for_name(group) if group else None

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
            user = self.user, group = group, request = self.request
        )
        print(msg)
        comment = UnassignAction.UNASSIGN_COMMENT.format(
            prefix = PREFIX, user = self.user, group = group
        )
        undo_comment = AssignAction.ASSIGN_COMMENT.format(
            prefix = PREFIX, user = self.user, group = group
        )
        self.request.review_reopen(group = group,
                                   comment = comment)
        self.undo_stack.append(
            lambda: self.request.review_accept(group = group,
                                               comment = undo_comment)
        )
        self.request.review_accept(user = self.user, comment = comment)
        self.undo_stack.append(
            lambda: self.request.review_reopen(user = self.user)
        )


class ApproveAction(OscAction):
    """Approve a review for a user.

    """
    APPROVE_MSG = "Will approve {request} for {user}."

    def __init__(self, remote, user, request_id, template_factory = Template):
        super(ApproveAction, self).__init__(remote, user)
        self.request = remote.requests.by_id(request_id)
        self.template = self.request.get_template(template_factory)

    def validate(self):
        """Check preconditions to be met before a request can be approved.

        :raises: :class:`oscqam.models.TestResultMismatchError` or
            :class:`oscqam.models.TestPlanReviewerNotSetError` if conditions
            are not met.

        """
        self.template.testplanreviewer()
        self.template.passed()

    def action(self):
        self.validate()
        msg = ApproveAction.APPROVE_MSG.format(user = self.user,
                                               request = self.request)
        print(msg)
        self.request.review_accept(user = self.user)


class RejectAction(OscAction):
    """Reject a request for a user and group.

    Attempts to automatically find the group that the user assigned himself
    for and will reject that group if possible.

    """
    DECLINE_MSG = "Will decline {request} for {user}."

    def __init__(self, remote, user, request_id, message = None):
        super(RejectAction, self).__init__(remote, user)
        self.request = remote.requests.by_id(request_id)
        self._template = None
        self.message = message

    @property
    def template(self):
        if not self._template:
            self._template = Template(self.request)
        return self._template

    def action(self):
        self.template.failed()
        comment = self.template.log_entries['comment']
        if self.message or not comment:
            comment = self.message
        msg = RejectAction.DECLINE_MSG.format(user = self.user,
                                              request = self.request)
        print(msg)
        if not comment:
            raise ActionError("Must provide a message for reject.")
        self.request.review_decline(user = self.user, comment = comment)


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
