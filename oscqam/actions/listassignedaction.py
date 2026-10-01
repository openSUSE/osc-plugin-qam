"""Provides an action to list assigned requests."""

from typing import ClassVar

from ..fields import ReportField
from .listaction import ListAction


class ListAssignedAction(ListAction):
    """Action to list assigned requests.

    Attributes:
        default_fields: A list of fields to display by default.
    """

    default_fields: ClassVar[list[ReportField]] = [
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
        return any(review.reviewer == self.user and review.open for review in reviews)

    def load_requests(self):
        """Loads all requests that are in review for QAM groups.

        Returns:
            A set of requests.
        """
        qam_groups = [
            group for group in self.remote.groups.all() if group.is_qam_group()
        ]
        return set(self.remote.requests.review_for_groups(qam_groups))
