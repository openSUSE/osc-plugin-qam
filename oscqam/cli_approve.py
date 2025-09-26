"""Provides a command-line interface for approving requests."""

import osc.commandline

from oscqam.actions import ApproveGroupAction, ApproveUserAction
from oscqam.common import Common


class QAMApproveCommand(osc.commandline.OscCommand, Common):
    """Approve the request for the user.

    This command allows a user to approve a request, either for themselves or
    for a group.
    """

    name = "approve"
    parent = "QAMCommand"

    def init_arguments(self):
        """Initializes the command-line arguments for the command."""
        self.add_argument(
            "-G",
            "--group",
            help="Group to *directly* approve for this request."
            "Only for groups that do not need reviews",
        )
        self.add_argument("request_id", type=str, help="ID of review request")
        self.add_argument(
            "--skip-template",
            action="store_true",
            help="Do not check template exists.",
        )

    def run(self, args):
        """Runs the command.

        Args:
            args: The command-line arguments.
        """
        self.set_required_params(args)
        if args.group:
            if self.yes_no(
                "This can *NOT* be used to accept a specific group "
                "you are reviewing. "
                "It will only accept the group's review. "
                "This can bring the update into an inconsistent state.\n"
                "You probably only want to run 'osc qam approve'.\nAbort?",
                default="yes",
            ):
                return
            action = ApproveGroupAction(
                self.api,
                self.affected_user,
                args.request_id,
                args.group,
                args.skip_template,
            )
        else:
            action = ApproveUserAction(
                self.api,
                self.affected_user,
                args.request_id,
                self.affected_user,
                args.skip_template,
            )
        action()
