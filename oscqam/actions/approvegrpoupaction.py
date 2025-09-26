"""Provides an action to approve a request for a group."""

from ..errors import NonMatchingGroupsError
from .approveaction import ApproveAction


class ApproveGroupAction(ApproveAction):
    """Approves a request for a group.

    Attributes:
        APPROVE_MSG: The message to use when approving the request.
    """

    APPROVE_MSG = "Approving {request} for group {group}."

    def get_reviewer(self, reviewer):
        """Gets the reviewer object for the given reviewer name.

        Args:
            reviewer: The name of the reviewer group.

        Returns:
            The reviewer object.
        """
        return self.remote.groups.for_name(reviewer)

    def validate(self):
        """Validates that the reviewer is a valid reviewer for the request.

        Raises:
            NonMatchingGroupsError: If the reviewer is not a valid reviewer for
                the request.
        """
        if self.reviewer not in self.request.groups:
            raise NonMatchingGroupsError([self.reviewer], self.request.groups)

    def action(self):
        """Performs the approval action."""
        self.validate()
        msg = self.APPROVE_MSG.format(request=self.request, group=self.reviewer)
        self.print(msg)
        self.request.review_accept(group=self.reviewer, comment=msg)
