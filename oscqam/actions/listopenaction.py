from ..errors import ReportedError
from .listaction import ListAction


class ListOpenAction(ListAction):
    def load_requests(self):
        def assigned(req):
            """Check if the request is assigned to the user that requests the
            listing."""
            for review in req.assigned_roles:
                if review.reviewer == self.user:
                    return True
            return False

        def filters(req):
            return req.active() and assigned(req)

        user_requests = {
            req for req in self.remote.requests.for_user(self.user) if filters(req)
        }
        qam_groups = self.user.qam_groups
        if not qam_groups:
            raise ReportedError(
                "You are not part of a qam group. Can not list requests."
            )
        group_requests = set(self.remote.requests.open_for_groups(qam_groups))
        return self.merge_requests(user_requests, group_requests)
