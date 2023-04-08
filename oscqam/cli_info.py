import osc.commandline

from oscqam.actions import InfoAction
from oscqam.common import Common
from oscqam.errors import ConflictingOptions
from oscqam.fields import ReportFields


class QAMInfoCommand(osc.commandline.OscCommand, Common):
    """Show information for the given request."""

    name = "info"
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
        self.add_argument("request_id", type=int, help="ID of review request")
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
        fields = ReportFields.review_fields_by_opts(args)
        action = InfoAction(self.api, self.affected_user, str(args.request_id))
        keys = fields.fields(action)
        self.list_requests(action, args.tabular, keys)
