"""Provides an action to delete a comment."""

from .oscaction import OscAction


class DeleteCommentAction(OscAction):
    """Delete a comment.

    Attributes:
        comment_id: The ID of the comment to delete.
    """

    def __init__(self, remote, user, comment_id):
        """Initializes a DeleteCommentAction.

        Args:
            remote: A remote facade.
            user: The user deleting the comment.
            comment_id: The ID of the comment to delete.
        """
        super().__init__(remote, user)
        self.comment_id = comment_id

    def action(self):
        """Deletes the comment."""
        self.remote.comments.delete(self.comment_id)
