"""Provides an action to list assigned requests."""

from ..fields import ReportField
from .listaction import ListAction


class ListAssignedAction(ListAction):
    """Action to list assigned requests.

    Attributes:
        default_fields: A list of fields to display by default.
    """

    default_fields = [
        ReportField.review_request_id,
        ReportField.srcrpms,
        ReportField.rating,
        ReportField.products,
        ReportField.incident_priority,
        ReportField.assigned_roles,
        ReportField.creator,
    ]

    def in_review_by_user(self, reviews):
        """Checks if a request is in review by the current user.

        Args:
            reviews: A list of reviews.

        Returns:
            True if the request is in review by the current user, False otherwise.
        """
        for review in reviews:
            if review.reviewer == self.user and review.open:
                return True
        return False

    def load_requests(self):
        """Loads all requests that are in review for QAM groups.

        Returns:
            A set of requests.
        """
        qam_groups = [
            group for group in self.remote.groups.all() if group.is_qam_group()
        ]
        return {
            request for request in self.remote.requests.review_for_groups(qam_groups)
        }
