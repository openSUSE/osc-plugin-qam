import logging

from ..errors import NoReviewError
from .oscaction import OscAction


class UnassignAction(OscAction):
    """Will unassign the user from the review and reopen the request for
    the group the user assign himself for.
    """

    UNASSIGN_MSG = "Unassigning {user} from {request} for group {group}."

    def __init__(self, remote, user, request_id, groups=None, **kwargs):
        super().__init__(remote, user, **kwargs)
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
            self.print("UNDO: Undoing reopening of group {group}".format(group=group))
            self.request.review_accept(group=group, comment=comment)

        return _

    def undo_accept(self, user):
        def _():
            self.print("UNDO: Undoing accepting user {user}".format(user=user))
            self.request.review_reopen(user=self.user)

        return _

    # TODO: this action should check and unassign only groups assigned to user..
    def unassign(self, groups, user_assigned_groups):
        for group in groups:
            msg = UnassignAction.UNASSIGN_MSG.format(
                user=self.user, group=group, request=self.request
            )
            self.print(msg)
            logging.debug(
                "Reverting assignment from %s back to %s" % (group, self.user)
            )
            self.request.review_unassign(reviewer=self.user, group=group, comment=msg)
