"""Provides an action to approve a request for a user."""

from ..errors import NoQamReviewsError, NonMatchingUserGroupsError, NotAssignedError
from .approveaction import ApproveAction


class ApproveUserAction(ApproveAction):
    """Approve a review for a user.

    Attributes:
        APPROVE_MSG: The message to use when approving the request.
        MORE_GROUPS_MSG: The message to use when there are more groups to review.
    """

    APPROVE_MSG = "Approving {request} for {user} ({groups}). Testreport: {url}"
    MORE_GROUPS_MSG = "The following groups could also be reviewed by you: {groups}"

    def get_reviewer(self, reviewer):
        """Gets the reviewer object for the given reviewer name.

        Args:
            reviewer: The name of the reviewer.

        Returns:
            The reviewer object.
        """
        return self.remote.users.by_name(reviewer)

    def reviews_assigned(self):
        """Ensure that the user was assigned before accepting.

        Returns:
            True if the user was assigned, False otherwise.

        Raises:
            NotAssignedError: If the user was not assigned to the request.
        """
        for review in self.request.assigned_roles:
            if review.user == self.user:
                return True
        else:
            raise NotAssignedError(self.user)

    def validate(self):
        """Check preconditions to be met before a request can be approved.

        Raises:
            TestResultMismatchError: if conditions are not met.
        """
        self.reviews_assigned()
        if self.template:
            self.template.passed()

    def additional_reviews(self):
        """Return groups that could also be reviewed by the user.

        Returns:
            A list of groups that could also be reviewed by the user.
        """
        return self.user.reviewable_groups(self.request)

    def action(self):
        """Performs the approval action."""
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
