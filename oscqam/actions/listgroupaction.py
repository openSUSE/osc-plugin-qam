from ..models import Template
from .listaction import ListAction


class ListGroupAction(ListAction):
    def __init__(self, remote, user, groups, template_factory=Template):
        super().__init__(remote, user, template_factory)
        if not groups:
            raise AttributeError("Can not list groups without any groups.")
        self.groups = [self.remote.groups.for_name(group) for group in groups]

    def load_requests(self):
        return {self.remote.requests.open_for_groups(self.groups)}
