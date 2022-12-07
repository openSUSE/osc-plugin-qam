from ..errors import (
    NotPreviousReviewerError,
    ReportNotYetGeneratedError,
    TemplateNotFoundError,
    UninferableError,
)
from ..models import Request, Template, UserReview
from .oscaction import OscAction


class AssignAction(OscAction):
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
        **kwargs
    ):
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
        """
        try:
            self.request.get_template(self.template_factory)
        except TemplateNotFoundError as e:
            raise ReportNotYetGeneratedError(self.request, str(e))

    def check_previous_rejects(self):
        """If there were previous rejects for an incident users that have
        already reviewed this incident should (preferably) review it again.

        If the user trying to assign himself is not one of the previous
        reviewers a warning is issued.
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
                AssignAction.MULTIPLE_GROUPS_MSG.format(groups=[str(g) for g in groups])
            )
        group = groups.pop()
        self.print(AssignAction.AUTO_INFER_MSG.format(group=group))
        return [group]

    def assign(self, groups):
        self.validate()
        for group in groups:
            msg = AssignAction.ASSIGN_MSG.format(
                user=self.user, group=group, request=self.request
            )
            self.request.review_assign(reviewer=self.user, group=group, comment=msg)
            self.print(msg)
