import osc.commandline

from oscqam.actions import UnassignAction
from oscqam.common import Common


class QAMUnassignCommand(osc.commandline.OscCommand, Common):
    """Unassign the request for the user.

    The command either uses the configured user or the user passed via
    the `-U` flag.

    It will attempt to automatically find the group that the user is
    reviewing for.  If the group can not be automatically determined it
    must be passed as an argument.
    """

    name = "unassign"
    parent = "QAMCommand"

    def init_arguments(self):
        self.add_argument("request_id", type=str, help="ID of review request")
        self.add_argument("-U", "--user", help="User to assign for this request.")
        self.add_argument(
            "-G",
            "--group",
            action="append",
            help="Groups to reassign to this request."
            "Pass multiple groups passing flag multiple times.",
        )

    def run(self, args):
        self.set_required_params(args)

        group = args.group if args.group else None
        action = UnassignAction(self.api, self.affected_user, args.request_id, group)
        action()
