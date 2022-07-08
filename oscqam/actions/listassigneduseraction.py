from .listassignedaction import ListAssignedAction


class ListAssignedUserAction(ListAssignedAction):
    """Action to list requests that are assigned to the user."""

    def load_requests(self):
        user_requests = set(self.remote.requests.for_user(self.user))
        return {
            request
            for request in user_requests
            if self.in_review_by_user(request.review_list())
        }
