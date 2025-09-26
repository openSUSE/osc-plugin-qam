"""Provides a command-line interface for deleting comments from requests."""

import osc.commandline

from oscqam.actions import DeleteCommentAction
from oscqam.common import Common
from oscqam.errors import InvalidCommentIdError, NoCommentsError


class QAMDeleteCommentCommand(osc.commandline.OscCommand, Common):
    """Remove a comment for the given request.

    The command will list all available comments of the request to allow
    choosing the one to remove.
    """

    name = "deletecomment"
    parent = "QAMCommand"
    aliases = ["rmcomment"]

    def init_arguments(self):
        """Initializes the command-line arguments for the command."""
        self.add_argument("request_id", type=str, help="ID of review request")

    def run(self, args):
        """Runs the command.

        Args:
            args: The command-line arguments.

        Raises:
            NoCommentsError: If the request has no comments.
            InvalidCommentIdError: If the user provides an invalid comment ID.
        """
        self.set_required_params(args)

        request = self.api.requests.by_id(args.request_id)

        if not request.comments:
            raise NoCommentsError()
        print("CommentID: Message")
        print("------------------")
        for comment in request.comments:
            print("{0}: {1}".format(comment.id, comment.text))
        comment_id = input("Comment-Id to remove: ")
        if comment_id not in [c.id for c in request.comments]:
            raise InvalidCommentIdError(comment_id, request.comments)
        action = DeleteCommentAction(self.api, self.affected_user, comment_id)
        action()
