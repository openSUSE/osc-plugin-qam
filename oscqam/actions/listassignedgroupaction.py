"""Provides an action to list requests assigned to a group."""

from ..models import Template
from .listassignedaction import ListAssignedAction


class ListAssignedGroupAction(ListAssignedAction):
    """Lists requests assigned to a specific group.

    Attributes:
        groups: A list of group objects.
    """

    def __init__(self, remote, user, groups, template_factory=Template):
        """Initializes a ListAssignedGroupAction.

        Args:
            remote: A remote facade.
            user: The user performing the action.
            groups: A list of group names.
            template_factory: A function to create a template.

        Raises:
            AttributeError: If no groups are provided.
        """
        super().__init__(remote, user, template_factory)
        if not groups:
            raise AttributeError("Can not list groups without any groups.")
        self.groups = [self.remote.groups.for_name(group) for group in groups]

    def in_review(self, reviews):
        """Checks if a request is in review by any of the specified groups.

        Args:
            reviews: A list of reviews.

        Returns:
            True if the request is in review by any of the specified groups,
            False otherwise.
        """
        for review in reviews:
            if review.reviewer in self.groups:
                return True
        return False

    def load_requests(self):
        """Loads all requests that are in review for the specified groups.

        Returns:
            A set of requests.
        """
        group_requests = set(self.remote.requests.review_for_groups(self.groups))
        return {
            request
            for request in group_requests
            if self.in_review(request.review_list())
        }
