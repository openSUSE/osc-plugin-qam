"""Provides an action to list requests assigned to a user."""

from .listassignedaction import ListAssignedAction


class ListAssignedUserAction(ListAssignedAction):
    """Action to list requests that are assigned to the user."""

    def load_requests(self):
        """Loads all requests that are assigned to the current user.

        Returns:
            A set of requests.
        """
        user_requests = set(self.remote.requests.for_user(self.user))
        return {
            request
            for request in user_requests
            if self.in_review_by_user(request.review_list())
        }
