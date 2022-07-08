from ..models import Template
from .listassignedaction import ListAssignedAction


class ListAssignedGroupAction(ListAssignedAction):
    def __init__(self, remote, user, groups, template_factory=Template):
        super().__init__(remote, user, template_factory)
        if not groups:
            raise AttributeError("Can not list groups without any groups.")
        self.groups = [self.remote.groups.for_name(group) for group in groups]

    def in_review(self, reviews):
        for review in reviews:
            if review.reviewer in self.groups:
                return True
        return False

    def load_requests(self):
        group_requests = set(self.remote.requests.review_for_groups(self.groups))
        return {
            request
            for request in group_requests
            if self.in_review(request.review_list())
        }
