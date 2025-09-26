"""Provides a command-line interface for listing assigned requests."""

import osc.commandline

from oscqam.actions import (
    ListAssignedAction,
    ListAssignedGroupAction,
    ListAssignedUserAction,
)
from oscqam.common import Common
from oscqam.errors import ConflictingOptions
from oscqam.fields import ReportFields


class QAMAssignedCommand(osc.commandline.OscCommand, Common):
    """Show a list of OBS qam-requests that are in review.

    A request is in review, as soon as a user has been assigned for a
    group that is required to review a request.
    """

    name = "assigned"
    parent = "QAMCommand"

    def init_arguments(self):
        """Initializes the command-line arguments for the command."""
        self.add_argument(
            "-G",
            "--group",
            action="append",
            default=[],
            help="Only requests containing assigned reviews for the  "
            "given groups will be output.",
        )
        self.add_argument(
            "-F",
            "--fields",
            action="append",
            default=[],
            help="Define the values to output in a cumulative fashion "
            "(pass flag multiple times).  "
            "Available fields: " + self.all_columns_string + ".",
        )
        self.add_argument(
            "-U",
            "--user",
            default=None,
            help="List requests assigned to the given USER.",
        )
        self.add_argument(
            "-T",
            "--tabular",
            action="store_true",
            help="Output the requests in an ASCII-table.",
        )
        self.add_argument(
            "-V",
            "--describe-fields",
            action="store_true",
            help="Display all available fields for a request: "
            + self.all_columns_string
            + ".",
        )

    def run(self, args):
        """Runs the command.

        Args:
            args: The command-line arguments.

        Raises:
            ConflictingOptions: If conflicting options are provided.
        """
        if args.verbose and args.fields:
            raise ConflictingOptions("Only pass '-v' or '-F' not both")
        if args.user and args.group:
            raise ConflictingOptions("Only pass '-U' or '-G' not both")
        self.set_required_params(args)
        fields = ReportFields.review_fields_by_opts(args)
        if args.user:
            action = ListAssignedUserAction(self.api, self.affected_user)
        elif args.group:
            action = ListAssignedGroupAction(self.api, self.affected_user, args.group)
        else:
            action = ListAssignedAction(self.api, self.affected_user)
        keys = fields.fields(action)
        self.list_requests(action, args.tabular, keys)
