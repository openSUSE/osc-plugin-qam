import osc.commandline

from oscqam.actions import AssignAction
from oscqam.common import Common
from oscqam.errors import NotPreviousReviewerError


class QAMAssignCommand(osc.commandline.OscCommand, Common):
    """Assign the request to the user.

    The command either uses the user that runs the osc command or the user
    that was passed as part of the command via the -U flag.

    It will attempt to automatically find a group that is not currently
    reviewed, but that the user could review for.  If no group can be
    automatically determined a group must be passed as an argument."""

    name = "assign"
    parent = "QAMCommand"

    def init_arguments(self):
        self.add_argument("request_id", type=str, help="ID of review request")
        self.add_argument("-U", "--user", help="User to assign for this request.")
        self.add_argument(
            "-G",
            "--group",
            action="append",
            help="Groups to assign the user for."
            "Pass multiple groups passing flag multiple times.",
        )
        self.add_argument(
            "--skip-template",
            action="store_true",
            help="Do not check whether a template exists.",
        )

    def run(self, args) -> None:
        self.set_required_params(args)
        group = args.group if args.group else None
        template_required: bool = args.skip_template
        action = AssignAction(
            self.api,
            self.affected_user,
            args.request_id,
            group,
            template_required=template_required,
        )
        try:
            action()
        except NotPreviousReviewerError as e:
            print(str(e))
            force = self.yes_no("Do you still want to assign yourself?")
            if not force:
                return
            action = AssignAction(
                self.api, self.affected_user, args.request_id, group, force=force
            )
            action()
