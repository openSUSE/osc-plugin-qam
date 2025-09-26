"""Provides a command-line interface for rejecting requests."""

import osc.commandline

from oscqam.actions import RejectAction
from oscqam.common import Common
from oscqam.reject_reasons import RejectReason


class QAMRejectCommand(osc.commandline.OscCommand, Common):
    """Reject the request for the user.

    The command either uses the configured user or the user passed via
    the `-U` flag.
    """

    name = "reject"
    parent = "QAMCommand"

    def init_arguments(self):
        """Initializes the command-line arguments for the command."""
        self.add_argument("request_id", type=str, help="ID of review request")
        self.add_argument("-U", "--user", help="User that rejects this request.")
        self.add_argument(
            "-M", "--message", help="Message to use for rejection-comment."
        )
        self.add_argument(
            "-R",
            "--reason",
            action="append",
            help="Reason the request was rejected: " + self.all_reasons_string,
        )
        self.add_argument(
            "--skip-template",
            action="store_true",
            help="Do not check whether a template exists.",
        )

    def run(self, args) -> None:
        """Runs the command.

        Args:
            args: The command-line arguments.
        """
        message = args.message if args.message else None
        reasons = (
            [RejectReason.from_str(r) for r in args.reason]
            if args.reason
            else self.query_enum(RejectReason, lambda r: r.enum_id, lambda r: r.text)
        )
        if reasons == self.SUBQUERY_QUIT:
            return
        self.set_required_params(args)
        template_skip: bool = False if args.skip_template else True
        action = RejectAction(
            self.api,
            self.affected_user,
            args.request_id,
            reasons,
            template_skip,
            message,
        )
        action()
