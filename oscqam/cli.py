from __future__ import print_function
import logging
import os
import prettytable
import sys
from osc import cmdln
import osc.commandline
import osc.conf

from oscqam.actions import (ApproveAction, AssignAction, ListOpenAction,
                            ListAssignedAction, ListAssignedUserAction,
                            UnassignAction, RejectAction, CommentAction,
                            InfoAction)
from oscqam.models import (RemoteFacade, ReportedError)
from oscqam.fields import ReportFields

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ConflictingOptions(ReportedError):
    pass


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
    length = max([len(str(k)) for k in keys])
    output = []
    str_template = "{{0:{length}s}}: {{1}}".format(length = length)
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
    INTERPRETER_QUIT = 3

    def __init__(self, parent_cmdln, *args, **kwargs):
        cmdln.Cmdln.__init__(self, *args, **kwargs)
        self.parent_cmdln = parent_cmdln

    name = 'osc qam'
    all_columns_string = ", ".join([str(f) for f in ReportFields.all_fields])

    def _set_required_params(self, opts):
        self.parent_cmdln.postoptparse()
        self.apiurl = self.parent_cmdln.get_api_url()
        self.api = RemoteFacade(self.apiurl)
        self.affected_user = None
        if hasattr(opts, 'user') and opts.user:
            self.affected_user = opts.user
        else:
            self.affected_user = osc.conf.get_apiurl_usr(self.apiurl)

    @cmdln.option('-U',
                  '--user',
                  help = 'User to assign for this request.')
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
        action()

    @cmdln.option('-U',
                  '--user',
                  help = 'User to assign for this request.')
    @cmdln.option('-G',
                  '--group',
                  help = 'Group to assign the user for.')
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
        action()

    def _list_requests(self, action, tabular, keys):
        """Display the requests from the action.

        :param action: Action that obtains the requests.
        :type action: L{oscqam.actions.ListAction}.
        :param tabular: True if output should be formatted in a table.
        :type tabular: bool
        :param keys: The keys to output
        :type keys: [str]
        """
        listdata = action()
        formatter = tabular_output if tabular else verbose_output
        if listdata:
            listdata = [datum.values(keys)
                        for datum in listdata]
            print(formatter(listdata, keys))

    @cmdln.option('-F',
                  '--fields',
                  action = 'append',
                  default = [],
                  help = 'Define the values to output in a cumulative fashion '
                         '(pass flag multiple times).  '
                         'Available fields: ' + all_columns_string + '.')
    @cmdln.option('-U',
                  '--user',
                  default = None,
                  help = 'List requests assignable to the given USER '
                         '(USER is a member of a qam-group that has an open '
                         'review for the request).')
    @cmdln.option('-T',
                  '--tabular',
                  action = 'store_true',
                  default = False,
                  help = 'Output the requests in an ASCII-table.')
    @cmdln.option('-v',
                  '--verbose',
                  action = 'store_true',
                  default = False,
                  help = 'Display all available fields for a request: '
                         + all_columns_string + '.')
    @cmdln.alias('list')
    def do_open(self, subcmd, opts):
        """${cmd_name}: Show a list of OBS qam-requests that are open.

        By default, open requests assignable to yourself will be shown
        (currently assigned to a qam-group you are a member of).

        ${cmd_usage}
        ${cmd_option_list}
        """
        if opts.verbose and opts.fields:
            raise ConflictingOptions("Only pass '-v' or '-F' not both")
        self._set_required_params(opts)
        fields = ReportFields.review_fields_by_opts(opts)
        action = ListOpenAction(self.api, self.affected_user)
        keys = fields.fields(action)
        self._list_requests(action, opts.tabular, keys)

    @cmdln.option('-F',
                  '--fields',
                  action = 'append',
                  default = [],
                  help = 'Define the values to output in a cumulative fashion '
                         '(pass flag multiple times).  '
                         'Available fields: ' + all_columns_string + '.')
    @cmdln.option('-U',
                  '--user',
                  default = None,
                  help = 'List requests assigned to the given USER.')
    @cmdln.option('-T',
                  '--tabular',
                  action = 'store_true',
                  default = False,
                  help = 'Output the requests in an ASCII-table.')
    @cmdln.option('-v',
                  '--verbose',
                  action = 'store_true',
                  default = False,
                  help = 'Display all available fields for a request: '
                         + all_columns_string + '.')
    def do_assigned(self, subcmd, opts):
        """${cmd_name}: Show a list of OBS qam-requests that are in review.

        A request is in review, as soon as a user has been assigned for a
        group that is required to review a request.

        ${cmd_usage}
        ${cmd_option_list}
        """
        if opts.verbose and opts.fields:
            raise ConflictingOptions("Only pass '-v' or '-F' not both")
        self._set_required_params(opts)
        fields = ReportFields.review_fields_by_opts(opts)
        if opts.user:
            action = ListAssignedUserAction(self.api, self.affected_user)
        else:
            action = ListAssignedAction(self.api, self.affected_user)
        keys = fields.fields(action)
        self._list_requests(action, opts.tabular, keys)

    @cmdln.option('-F',
                  '--fields',
                  action = 'append',
                  default = [],
                  help = 'Define the values to output in a cumulative fashion '
                         '(pass flag multiple times).  '
                         'Available fields: ' + all_columns_string + '.')
    @cmdln.option('-T',
                  '--tabular',
                  action = 'store_true',
                  default = False,
                  help = 'Output the requests in an ASCII-table.')
    @cmdln.option('-v',
                  '--verbose',
                  action = 'store_true',
                  default = False,
                  help = 'Display all available fields for a request: '
                         + all_columns_string + '.')
    def do_info(self, subcmd, opts, request_id):
        """${cmd_name}: Show information for the given request.
        """
        if opts.verbose and opts.fields:
            raise ConflictingOptions("Only pass '-v' or '-F' not both")
        self._set_required_params(opts)
        fields = ReportFields.review_fields_by_opts(opts)
        action = InfoAction(self.api, self.affected_user, request_id)
        keys = fields.fields(action)
        self._list_requests(action, opts.tabular, keys)

    @cmdln.option('-U',
                  '--user',
                  help = 'User that rejects this request.')
    @cmdln.option('-M',
                  '--message',
                  help = 'Message to use for rejection-comment.')
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
        action()

    @cmdln.option('-U',
                  '--user',
                  help = 'User to assign for this request.')
    @cmdln.option('-G',
                  '--group',
                  help = 'Group to reassign to this request.')
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
        action()

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
        action()

    @cmdln.alias('q')
    @cmdln.alias('Q')
    def do_quit(self, subcmd, opts):
        """${cmd_name}: Quit the qam-subinterpreter."""
        self.stop = True
        return self.INTERPRETER_QUIT


@cmdln.option('-A',
              '--assigned',
              action = 'store_true',
              help = 'Parameter for list command.')
@cmdln.option('-F',
              '--fields',
              action = 'append',
              help = 'Define the fields to output for the list command in '
                   'cumulative fashion (pass flag multiple times).')
@cmdln.option('-G',
              '--group',
              help = 'Group to use for the command.')
@cmdln.option('-M',
              '--message',
              help = 'Message to use for the command.')
@cmdln.option('-T',
              '--tabular',
              action = 'store_true',
              help = 'Create tabular output for list command.')
@cmdln.option('-U',
              '--user',
              help = 'User to use for the command.')
@cmdln.option('-v',
              '--verbose',
              action = 'store_true',
              help = 'Generate verbose output.')
def do_qam(self, subcmd, opts, *args, **kwargs):
    """Start the QA-Maintenance specific submode of osc for request handling.
    """
    osc_stdout = [None]
    retval = None

    def restore_orig_stdout():
        """osc is replacing the stdout with their own writer-class.

        This prevents readline from working, which is annoying for a
        interactive commandline application.

        """
        osc_stdout[0] = sys.stdout
        sys.stdout = osc_stdout[0].__dict__['writer']

    def restore_osc_stdout():
        """When the plugin has finished running restore the osc-state.

        """
        sys.stdout = osc_stdout[0]
    osc.conf.get_config()
    running = True
    ret = None
    while running:
        try:
            restore_orig_stdout()
            interp = QamInterpreter(self)
            interp.optparser = cmdln.SubCmdOptionParser()
            if args:
                running = False
                index = sys.argv.index('qam')
                ret = interp.onecmd(sys.argv[index + 1:])
            else:
                ret = interp.cmdloop()
                if ret == QamInterpreter.INTERPRETER_QUIT:
                    running = False
        except ReportedError as e:
            print(str(e))
        finally:
            restore_osc_stdout()
    return ret
