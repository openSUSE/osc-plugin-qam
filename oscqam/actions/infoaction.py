from .listaction import ListAction
from ..fields import ReportField


class InfoAction(ListAction):
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
        super().__init__(remote, user_id)
        self.request = remote.requests.by_id(request_id)

    def load_requests(self):
        return [self.request]
