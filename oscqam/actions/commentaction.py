"""Provides an action to add a comment to a request."""

from .oscaction import OscAction


class CommentAction(OscAction):
    """Add a comment to a request.

    Attributes:
        comment: The comment to add.
        request: The request to add the comment to.
    """

    def __init__(self, remote, user, request_id, comment):
        """Initializes a CommentAction.

        Args:
            remote: A remote facade.
            user: The user adding the comment.
            request_id: The ID of the request to add the comment to.
            comment: The comment to add.
        """
        super().__init__(remote, user)
        self.comment = comment
        self.request = remote.requests.by_id(request_id)

    def action(self):
        """Adds the comment to the request."""
        self.request.add_comment(self.comment)
