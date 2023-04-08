import osc.commandline

from oscqam.actions import ApproveGroupAction, ApproveUserAction
from oscqam.common import Common


class QAMApproveCommand(osc.commandline.OscCommand, Common):
    """Approve the request for the user"""

    name = "approve"
    parent = "QAMCommand"

    def init_arguments(self):
        self.add_argument(
            "-G",
            "--group",
            help="Group to *directly* approve for this request."
            "Only for groups that do not need reviews",
        )
        self.add_argument("request_id", type=int, help="ID of review request")

    def run(self, args):
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
                self.api, self.affected_user, args.request_id, args.group
            )
        else:
            action = ApproveUserAction(
                self.api, self.affected_user, str(args.request_id), self.affected_user
            )
        action()
