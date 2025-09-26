"""Provides an action to get information about a request."""

from .listaction import ListAction
from ..fields import ReportField


class InfoAction(ListAction):
    """Gets information about a request.

    Attributes:
        default_fields: A list of fields to display by default.
        request: The request to get information about.
    """

    default_fields = [
        ReportField.review_request_id,
        ReportField.srcrpms,
        ReportField.rating,
        ReportField.products,
        ReportField.incident_priority,
        ReportField.assigned_roles,
        ReportField.unassigned_roles,
        ReportField.creator,
        ReportField.issues,
    ]

    def __init__(self, remote, user_id, request_id):
        """Initializes an InfoAction.

        Args:
            remote: A remote facade.
            user_id: The ID of the user getting the information.
            request_id: The ID of the request to get information about.
        """
        super().__init__(remote, user_id)
        self.request = remote.requests.by_id(request_id)

    def load_requests(self):
        """Loads the request.

        Returns:
            A list containing the request.
        """
        return [self.request]
