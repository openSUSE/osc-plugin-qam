from ..errors import NonMatchingGroupsError
from .approveaction import ApproveAction


class ApproveGroupAction(ApproveAction):
    APPROVE_MSG = "Approving {request} for group {group}."

    def get_reviewer(self, reviewer):
        return self.remote.groups.for_name(reviewer)

    def validate(self):
        if self.reviewer not in self.request.groups:
            raise NonMatchingGroupsError([self.reviewer], self.request.groups)

    def action(self):
        self.validate()
        msg = self.APPROVE_MSG.format(request=self.request, group=self.reviewer)
        self.print(msg)
        self.request.review_accept(group=self.reviewer, comment=msg)
