"""Provides an action to list open requests for a group."""

from ..models import Template
from .listaction import ListAction


class ListGroupAction(ListAction):
    """Lists open requests for a specific group.

    Attributes:
        groups: A list of group objects.
    """

    def __init__(self, remote, user, groups, template_factory=Template):
        """Initializes a ListGroupAction.

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

    def load_requests(self):
        """Loads all open requests for the specified groups.

        Returns:
            A set of requests.
        """
        return set(self.remote.requests.open_for_groups(self.groups))
