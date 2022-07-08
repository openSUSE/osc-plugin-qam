from .oscaction import OscAction


class DeleteCommentAction(OscAction):
    """Delete a comment."""

    def __init__(self, remote, user, comment_id):
        super().__init__(remote, user)
        self.comment_id = comment_id

    def action(self):
        self.remote.comments.delete(self.comment_id)
