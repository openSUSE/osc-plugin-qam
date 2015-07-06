from __future__ import print_function
import itertools
import logging
import os
import prettytable
import sys
from osc import cmdln
import osc.commandline
import osc.conf

from oscqam.actions import (ApproveAction, AssignAction, ListAction,
                            UnassignAction, RejectAction, CommentAction)
from oscqam.models import (RemoteFacade, ReportedError)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def multi_level_sort(xs, criteria):
    """Sort the given collection based on multiple criteria.
    The criteria will be sorted by in the given order, whereas each group
    from the first criteria will be sorted by the second criteria and so forth.

    :param xs: Iterable of objects.
    :type xs: [a]

    :param criteria: Iterable of extractor functions.
    :type criteria: [a -> b]

    """
    if not criteria:
        return xs
    extractor = criteria[-1]
    xss = sorted(xs, key = extractor)
    grouped = itertools.groupby(xss, extractor)
    subsorts = [multi_level_sort(list(value), criteria[:-1]) for _, value in
                grouped]
    return [s for sub in subsorts for s in sub]


def group_sort_requests(requests):
    """Sort request according to rating and request id.

    First sort by Priority, then rating and finally request id.
    """
    requests = filter(None, requests)
    return multi_level_sort(requests, [lambda l: l.request.reqid,
                                       lambda l: l.template.log_entries["Rating"],
                                       lambda l: l.request.incident_priority])


def output_list(sep, value):
    """Join lists on the given separator and return strings unaltered.

    :param sep: Separator to join a list on.
    :type list_transform: str

    :param value: Output value.
    :type value: L{str} or list(L{str})

    :return: str
    """
    return sep.join(value) if isinstance(value, list) else value


def verbose_output(data, keys):
    """Output the data in verbose format."""
    length = max([len(k) for k in keys])
    output = []
    str_template = "{{0:{length}s}}: {{1}}".format(length=length)
    for row in data:
        for i, datum in enumerate(row):
            key = keys[i]
            datum = output_list(", ", datum)
            output.append(str_template.format(key, datum))
        output.append("-----------------------")
    return os.linesep.join(output)


def tabular_output(data, headers):
    """Format data for output in a table.

    Args:
        - headers: Headers of the table.
        - data: The data to be printed as a table. The data is expected to be
                provided as a list of lists: [[row1], [row2], [row3]]
    """
    table_formatter = prettytable.PrettyTable(headers)
    table_formatter.align = 'l'
    table_formatter.border = True
    for row in data:
        row = [output_list(os.linesep, value) for value in row]
        table_formatter.add_row(row)
    return table_formatter


class QamInterpreter(cmdln.Cmdln):
    """Usage: osc qam [command] [opts] [args]

    openSUSE build service command-line tool qam extensions.

    ${command_list}
    ${help_list}
    """
    def __init__(self, parent_cmdln, *args, **kwargs):
        cmdln.Cmdln.__init__(self, *args, **kwargs)
        self.parent_cmdln = parent_cmdln

    name = 'osc qam'
    all_keys = ["ReviewRequestID", "Products", "SRCRPMs", "Bugs",
                "Category", "Rating", "Unassigned Roles",
                "Assigned Roles", "Package-Streams", "Incident Priority"]
    all_columns_string = ", ".join(all_keys)

    def _set_required_params(self, opts):
        self.parent_cmdln.postoptparse()
        self.apiurl = self.parent_cmdln.get_api_url()
        self.api = RemoteFacade(self.apiurl)
        self.affected_user = None
        if hasattr(opts, 'user') and opts.user:
            self.affected_user = opts.user
        else:
            self.affected_user = osc.conf.get_apiurl_usr(self.apiurl)

    def _run_action(self, func):
        """Run the given action and catch (expected) errors that might occur.

        """
        try:
            return func()
        except ReportedError as e:
            print(str(e))

    @cmdln.option('-U',
                  '--user',
                  help='User to assign for this request.')
    def do_approve(self, subcmd, opts, request_id):
        """${cmd_name}: Approve the request for the user.

        The command either uses the user that runs the osc command or the user
        that was passed as part of the command via the -U flag.

        ${cmd_usage}
        ${cmd_option_list}
        """
        self._set_required_params(opts)
        self.request_id = request_id
        action = ApproveAction(self.api, self.affected_user, self.request_id)
        self._run_action(action)

    @cmdln.option('-U',
                  '--user',
                  help='User to assign for this request.')
    @cmdln.option('-G',
                  '--group',
                  help='Group to assign the user for.')
    def do_assign(self, subcmd, opts, request_id):
        """${cmd_name}: Assign the request to the user.

        The command either uses the user that runs the osc command or the user
        that was passed as part of the command via the -U flag.

        It will attempt to automatically find a group that is not currently
        reviewed, but that the user could review for.  If no group can be
        automatically determined a group must be passed as an argument.

        ${cmd_usage}
        ${cmd_option_list}
        """
        self._set_required_params(opts)
        self.request_id = request_id
        group = opts.group if opts.group else None
        action = AssignAction(self.api, self.affected_user, self.request_id,
                              group)
        self._run_action(action)

    @cmdln.option('-F',
                  '--fields',
                  action = 'append',
                  default = [],
                  help = 'Define the values to output in a cumulative fashion '
                         '(pass flag multiple times).  '
                         'Available fields: ' + all_columns_string + '.')
    @cmdln.option('-U',
                  '--user',
                  help='User to list requests for.')
    @cmdln.option('-R',
                  '--review',
                  action='store_true',
                  help='Show all requests that are in review by the user.')
    @cmdln.option('-T',
                  '--tabular',
                  action='store_true',
                  default=False,
                  help='Output the list in a tabular format.')
    @cmdln.option('-v',
                  '--verbose',
                  action='store_true',
                  default=False,
                  help='Generate verbose output.')
    def do_list(self, subcmd, opts):
        """${cmd_name}: Show a list of all open qam-requests currently running.

        The list will only contain requests that are part of the qam-groups.

        ${cmd_usage}
        ${cmd_option_list}
        """
        self._set_required_params(opts)
        only_review = opts.review if opts.review else False
        formatter = tabular_output if opts.tabular else verbose_output
        action = ListAction(self.api, self.affected_user, only_review)
        listdata = self._run_action(action)
        keys = ["ReviewRequestID", "SRCRPMs", "Rating", "Products",
                "Incident Priority"]
        if opts.verbose:
            keys = self.all_keys
        else:
            badcols = set(opts.fields) - set(self.all_keys)
            if len(badcols):
                print("Unknown fields: %s" % (", ".join(map(repr, badcols))))
                return
            elif opts.fields:
                keys = opts.fields

        if listdata:
            listdata = group_sort_requests(listdata)
            listdata = [datum.values(keys)
                        for datum in listdata]
            print(formatter(listdata, keys))

    @cmdln.option('-U',
                  '--user',
                  help='User that rejects this request.')
    @cmdln.option('-M',
                  '--message',
                  help='Message to use for rejection-comment.')
    def do_reject(self, subcmd, opts, request_id):
        """${cmd_name}: Reject the request for the user.

        The command either uses the configured user or the user passed via
        the `-u` flag.

        ${cmd_usage}
        ${cmd_option_list}
        """
        self._set_required_params(opts)
        self.request_id = request_id
        message = opts.message if opts.message else None
        action = RejectAction(self.api, self.affected_user, self.request_id,
                              message)
        self._run_action(action)

    @cmdln.option('-U',
                  '--user',
                  help='User to assign for this request.')
    @cmdln.option('-G',
                  '--group',
                  help='Group to reassign to this request.')
    def do_unassign(self, subcmd, opts, request_id):
        """${cmd_name}: Unassign the request for the user.

        The command either uses the configured user or the user passed via
        the `-u` flag.

        It will attempt to automatically find the group that the user is
        reviewing for.  If the group can not be automatically determined it
        must be passed as an argument.

        ${cmd_usage}
        ${cmd_option_list}
        """
        self._set_required_params(opts)
        self.request_id = request_id
        group = opts.group if opts.group else None
        action = UnassignAction(self.api, self.affected_user, self.request_id,
                                group)
        self._run_action(action)

    def do_comment(self, subcmd, opts, request_id, comment):
        """${cmd_name}: Add a comment to a request.

        The command will add a comment to the given request.

        ${cmd_usage}
        ${cmd_option_list}
        """
        self._set_required_params(opts)
        self.request_id = request_id
        action = CommentAction(self.api, self.affected_user, self.request_id,
                               comment)
        self._run_action(action)

    @cmdln.alias('q')
    @cmdln.alias('Q')
    def do_quit(self, subcmd, opts):
        """${cmd_name}: Quit the qam-subinterpreter."""
        self.stop = True


@cmdln.option('-F',
              '--fields',
              action = 'append',
              help = 'Define the fields to output for the list command in '
                   'cumulative fashion (pass flag multiple times).')
@cmdln.option('-G',
              '--group',
              help='Group to use for the command.')
@cmdln.option('-M',
              '--message',
              help='Message to use for the command.')
@cmdln.option('-R',
              '--review',
              action='store_true',
              help='Parameter for list command.')
@cmdln.option('-T',
              '--tabular',
              action='store_true',
              help='Create tabular output for list command.')
@cmdln.option('-U',
              '--user',
              help='User to use for the command.')
@cmdln.option('-v',
              '--verbose',
              action='store_true',
              help='Generate verbose output.')
def do_qam(self, subcmd, opts, *args, **kwargs):
    """Start the QA-Maintenance specific submode of osc for request handling.
    """
    osc_stdout = None
    retval = None

    def restore_orig_stdout():
        """osc is replacing the stdout with their own writer-class.

        This prevents readline from working, which is annoying for a
        interactive commandline application.

        """
        osc_stdout = sys.stdout
        sys.stdout = osc_stdout.__dict__['writer']

    def restore_osc_stdout():
        """When the plugin has finished running restore the osc-state.

        """
        sys.stdout = osc_stdout
    osc.conf.get_config()
    restore_orig_stdout()
    try:
        interp = QamInterpreter(self)
        interp.optparser = cmdln.SubCmdOptionParser()
        if args:
            index = sys.argv.index('qam')
            retval = interp.onecmd(sys.argv[index + 1:])
        else:
            retval = interp.cmdloop()
    finally:
        restore_osc_stdout()
    return retval
