"""Provides an action to unassign a user from a request."""

import logging

from ..errors import NoReviewError
from .oscaction import OscAction


class UnassignAction(OscAction):
    """Will unassign the user from the review and reopen the request for
    the group the user assign himself for.

    Attributes:
        UNASSIGN_MSG: The message to use when unassigning a user.
        request: The request to unassign the user from.
    """

    UNASSIGN_MSG = "Unassigning {user} from {request} for group {group}."

    def __init__(self, remote, user, request_id, groups=None, **kwargs):
        """Initializes an UnassignAction.

        Args:
            remote: A remote facade.
            user: The user to unassign.
            request_id: The ID of the request to unassign the user from.
            groups: A list of group names to unassign from. If None, the groups
                the user is reviewing will be used.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(remote, user, **kwargs)
        self.request = remote.requests.by_id(request_id)
        if groups:
            self._groups = [remote.groups.for_name(group) for group in groups]
        else:
            self._groups = None

    def groups(self):
        """Returns the groups to unassign from.

        If no groups were specified during initialization, this will return the
        groups the user is currently reviewing.

        Returns:
            A list of group objects.
        """
        if self._groups:
            return self._groups
        return self.review_groups()

    def action(self):
        """Performs the unassignment action."""
        assigned_groups = self.review_groups()
        self.unassign(self.groups(), assigned_groups)

    def review_groups(self):
        """Find the exact group the user is currently reviewing and return it.

        Returns:
            A list of groups in review by the user.

        Raises:
            NoReviewError: If the user is not reviewing any group of the
                request.
        """
        groups = self.user.in_review_groups(self.request)
        if not groups:
            raise NoReviewError(self.user)
        return groups

    def undo_reopen(self, group, comment):
        """Creates a function to undo a group reopen.

        Args:
            group: The group that was reopened.
            comment: The comment associated with the reopen.

        Returns:
            A function that will undo the reopen.
        """

        def _():
            self.print("UNDO: Undoing reopening of group {group}".format(group=group))
            self.request.review_accept(group=group, comment=comment)

        return _

    def undo_accept(self, user):
        """Creates a function to undo a user accept.

        Args:
            user: The user that was accepted.

        Returns:
            A function that will undo the accept.
        """

        def _():
            self.print("UNDO: Undoing accepting user {user}".format(user=user))
            self.request.review_reopen(user=self.user)

        return _

    # TODO: this action should check and unassign only groups assigned to user..
    def unassign(self, groups, user_assigned_groups):
        """Unassigns the user from the specified groups.

        Args:
            groups: The groups to unassign the user from.
            user_assigned_groups: The groups the user is actually assigned to.
        """
        for group in groups:
            msg = UnassignAction.UNASSIGN_MSG.format(
                user=self.user, group=group, request=self.request
            )
            self.print(msg)
            logging.debug(
                "Reverting assignment from %s back to %s" % (group, self.user)
            )
            self.request.review_unassign(reviewer=self.user, group=group, comment=msg)
