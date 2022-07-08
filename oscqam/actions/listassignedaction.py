from ..fields import ReportField
from .listaction import ListAction


class ListAssignedAction(ListAction):
    """Action to list assigned requests."""

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
        for review in reviews:
            if review.reviewer == self.user and review.open:
                return True
        return False

    def load_requests(self):
        qam_groups = [
            group for group in self.remote.groups.all() if group.is_qam_group()
        ]
        return {
            request for request in self.remote.requests.review_for_groups(qam_groups)
        }
