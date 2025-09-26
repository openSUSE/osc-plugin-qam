"""Provides an action to list open requests."""

from ..errors import ReportedError
from .listaction import ListAction


class ListOpenAction(ListAction):
    """Lists open requests for the current user and their QAM groups."""

    def load_requests(self):
        """Loads all open requests for the current user and their QAM groups.

        Returns:
            A set of requests.

        Raises:
            ReportedError: If the user is not part of any QAM group.
        """

        def assigned(req):
            """Check if the request is assigned to the user that requests the
            listing.

            Args:
                req: The request to check.

            Returns:
                True if the request is assigned to the current user, False
                otherwise.
            """
            for review in req.assigned_roles:
                if review.reviewer == self.user:
                    return True
            return False

        def filters(req):
            """Filters requests to only include active and assigned requests."""
            return req.active() and assigned(req)

        user_requests = {
            req for req in self.remote.requests.for_user(self.user) if filters(req)
        }
        qam_groups = self.user.qam_groups
        if not qam_groups:
            raise ReportedError(
                "You are not part of a qam group. Can not list requests."
            )
        group_requests = set(self.remote.requests.open_for_groups(qam_groups))
        return self.merge_requests(user_requests, group_requests)
