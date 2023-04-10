import osc.commandline

from oscqam.actions import CommentAction
from oscqam.common import Common
from oscqam.errors import MissingCommentError


class QAMCommentCommand(osc.commandline.OscCommand, Common):

    """Add a comment to a request.

    The command will add a comment to the given request."""

    name = "comment"
    parent = "QAMCommand"

    def init_arguments(self):
        self.add_argument("request_id", type=str, help="ID of review request")
        self.add_argument("comment", nargs="*", type=str, help="Text of comment")

    def run(self, args):
        self.set_required_params(args)
        if not args.comment:
            raise MissingCommentError

        comment = " ".join(args.comment)

        action = CommentAction(self.api, self.affected_user, args.request_id, comment)
        action()
