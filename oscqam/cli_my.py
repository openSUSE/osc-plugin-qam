import osc.commandline

from oscqam.actions import ListAssignedUserAction
from oscqam.common import Common
from oscqam.errors import ConflictingOptions
from oscqam.fields import ReportFields


class QAMMyCommand(osc.commandline.OscCommand, Common):
    """list ...."""

    name = "my"
    parent = "QAMCommand"

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

    def run(self, args):
        if args.describe_fields and args.fields:
            raise ConflictingOptions("Only pass '-v' or '-F' not both")
        self.set_required_params(args)
        args.user = self.affected_user
        fields = ReportFields.review_fields_by_opts(args)
        action = ListAssignedUserAction(self.api, self.affected_user)
        keys = fields.fields(action)
        self.list_requests(action, args.tabular, keys)
