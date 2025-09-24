from ..errors import NoQamReviewsError, NonMatchingUserGroupsError, NotAssignedError
from .approveaction import ApproveAction


class ApproveUserAction(ApproveAction):
    """Approve a review for a user."""

    APPROVE_MSG = "Approving {request} for {user} ({groups}). Testreport: {url}"
    MORE_GROUPS_MSG = "The following groups could also be reviewed by you: {groups}"

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

        :raises: :class:`oscqam.models.TestResultMismatchError` if conditions
        are not met.

        """
        self.reviews_assigned()
        if self.template:
            self.template.passed()

    def additional_reviews(self):
        """Return groups that could also be reviewed by the user."""
        return self.user.reviewable_groups(self.request)

    def action(self):
        self.validate()
        if self.template:
            url = self.template.fancy_url
        else:
            url = "no template"
        groups = ", ".join([str(g) for g in self.user.in_review_groups(self.request)])
        msg = self.APPROVE_MSG.format(
            user=self.reviewer, groups=groups, request=self.request, url=url
        )
        self.print(msg)
        self.request.review_accept(user=self.reviewer, comment=msg)
        try:
            groups = ", ".join(str(g) for g in self.additional_reviews())
            msg = self.MORE_GROUPS_MSG.format(groups=groups)
            self.print(msg)
        except NonMatchingUserGroupsError:
            pass
        except NoQamReviewsError:
            pass
