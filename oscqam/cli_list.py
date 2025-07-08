import osc.commandline

from oscqam.actions import ListGroupAction, ListOpenAction
from oscqam.common import Common
from oscqam.errors import ConflictingOptions
from oscqam.fields import ReportFields


class QAMListCommand(osc.commandline.OscCommand, Common):
    """Show a list of OBS qam-requests that are open.

    By default, open requests assignable to yourself will be shown
    (currently assigned to a qam-group you are a member of.)"""

    name = "list"
    parent = "QAMCommand"
    aliases = ["open"]

    def init_arguments(self):
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
        self.add_argument(
            "-G",
            "--group",
            action="append",
            help="Only requests containing open reviews for the given "
            "groups will be output.",
        )
        self.add_argument(
            "-U",
            "--user",
            default=None,
            help="List requests assignable to the given USER "
            "(USER is a member of a qam-group that has an open "
            "review for the request).",
        )

    def run(self, args):
        if args.describe_fields and args.fields:
            raise ConflictingOptions("Only pass '-v' or '-F' not both")
        self.set_required_params(args)
        fields = ReportFields.review_fields_by_opts(args)
        if args.group:
            action = ListGroupAction(self.api, self.affected_user, args.group)
        else:
            action = ListOpenAction(self.api, self.affected_user)
        keys = fields.fields(action)
        self.list_requests(action, args.tabular, keys)
