from .oscaction import OscAction


class CommentAction(OscAction):
    """Add a comment to a request."""

    def __init__(self, remote, user, request_id, comment):
        super().__init__(remote, user)
        self.comment = comment
        self.request = remote.requests.by_id(request_id)

    def action(self):
        self.request.add_comment(self.comment)
