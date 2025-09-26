"""Provides an action to assign a user to a request."""

from ..errors import (
    NoQamReviewsError,
    NotPreviousReviewerError,
    ReportNotYetGeneratedError,
    TemplateNotFoundError,
    UninferableError,
)
from ..models import Request, Template, UserReview
from .oscaction import OscAction


class AssignAction(OscAction):
    """Assigns a user to a request.

    Attributes:
        ASSIGN_MSG: The message to use when assigning a user.
        AUTO_INFER_MSG: The message to use when a group is auto-inferred.
        MULTIPLE_GROUPS_MSG: The message to use when multiple groups could be
            reviewed.
        request: The request to assign the user to.
        groups: The groups to assign the user to.
        template_factory: A function to get a template from.
        template_required: A boolean indicating whether a template is required.
        force: A boolean indicating whether to force the assignment.
    """

    ASSIGN_MSG = "Assigning {user} to {group} for {request}."
    AUTO_INFER_MSG = "Found a possible group: {group}."
    MULTIPLE_GROUPS_MSG = (
        "User could review more than one group: {groups}. "
        "Specify the group to review using the -G flag."
    )

    def __init__(
        self,
        remote,
        user,
        request_id,
        groups=None,
        template_factory=Template,
        force=False,
        template_required=True,
        **kwargs,
    ):
        """Initializes an AssignAction.

        Args:
            remote: A remote facade.
            user: The user to assign.
            request_id: The ID of the request to assign the user to.
            groups: The groups to assign the user to.
            template_factory: A function to get a template from.
            force: A boolean indicating whether to force the assignment.
            template_required: A boolean indicating whether a template is
                required.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(remote, user, **kwargs)
        self.request = remote.requests.by_id(request_id)
        self.groups = (
            [remote.groups.for_name(group) for group in groups] if groups else None
        )
        self.template_factory = template_factory
        self.template_required = template_required
        self.force = force

    def template_exists(self):
        """Check that the template associated with the request exists.

        If the template is not yet generated, assigning a user can lead
        to the template-generator no longer finding the request and
        never generating the template.

        Raises:
            ReportNotYetGeneratedError: If the template has not yet been
                generated.
        """
        try:
            self.request.get_template(self.template_factory)
        except TemplateNotFoundError as e:
            raise ReportNotYetGeneratedError(self.request, str(e))

    def check_open_review(self) -> None:
        """Checks that the request is in an open state.

        Raises:
            NoQamReviewsError: If the request is not in an open state.
        """
        if self.request.state.name not in Request.OPEN_STATES:
            raise NoQamReviewsError([])

    def check_previous_rejects(self):
        """If there were previous rejects for an incident users that have
        already reviewed this incident should (preferably) review it again.

        If the user trying to assign himself is not one of the previous
        reviewers a warning is issued.

        Raises:
            NotPreviousReviewerError: If the user is not a previous reviewer.
        """
        related_requests = self.remote.requests.for_incident(self.request.src_project)
        if not related_requests:
            return
        declined_requests = [
            request
            for request in related_requests
            if request.state.name == Request.STATE_DECLINED
        ]
        if not declined_requests:
            return
        reviewers = [
            review.reviewer
            for review in (request.review_list() for request in declined_requests)
            if isinstance(review, UserReview)
        ]
        if self.user not in reviewers:
            raise NotPreviousReviewerError(reviewers)

    def validate(self):
        """Validates the assignment."""
        # if tehere isn't open review all other cheks aren't required and can't be overridden by self.force
        self.check_open_review()
        if self.force:
            return
        if self.template_required:
            self.template_exists()
        self.check_previous_rejects()

    def action(self):
        """Performs the assignment action."""
        if self.groups:
            self.assign(self.groups)
        else:
            group = self.reviewable_group()
            # TODO: Ensure that the user actually wants this?
            self.assign(group)

    def reviewable_group(self):
        """Based on the given user and request search for a group that
        the user could do the review for.

        Returns:
            A list of groups that the user can review for.

        Raises:
            UninferableError: If the user can review for more than one group.
        """
        groups = self.user.reviewable_groups(self.request)
        if len(groups) > 1:
            raise UninferableError(
                AssignAction.MULTIPLE_GROUPS_MSG.format(groups=[str(g) for g in groups])
            )
        group = groups.pop()
        self.print(AssignAction.AUTO_INFER_MSG.format(group=group))
        return [group]

    def assign(self, groups):
        """Assigns the user to the given groups.

        Args:
            groups: The groups to assign the user to.
        """
        self.validate()
        for group in groups:
            msg = AssignAction.ASSIGN_MSG.format(
                user=self.user, group=group, request=self.request
            )
            self.request.review_assign(reviewer=self.user, group=group, comment=msg)
            self.print(msg)
