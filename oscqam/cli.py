from __future__ import print_function
from oscqam import strict_version
import logging
import sys
from osc import cmdln
import osc.commandline
import osc.conf

from oscqam.actions import (ApproveUserAction, ApproveGroupAction,
                            AssignAction, ListOpenAction, ListGroupAction,
                            ListAssignedGroupAction, ListAssignedAction,
                            ListAssignedUserAction, UnassignAction,
                            RejectAction, CommentAction, InfoAction,
                            DeleteCommentAction)
from oscqam.errors import NotPreviousReviewerError, ReportedError
from oscqam.formatters import VerboseOutput, TabularOutput
from oscqam.fields import ReportFields
from oscqam.remotes import RemoteFacade
from oscqam.reject_reasons import RejectReason

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ConflictingOptions(ReportedError):
    pass


class NoCommentsError(ReportedError):
    def __init__(self):
        super(NoCommentsError, self).__init__('No comments were found.')


class InvalidCommentIdError(ReportedError):
    def __init__(self, id, comments):
        msg = 'Id {0} is not in valid ids: {1}'.format(
            id, ', '.join([c.id for c in comments])
        )
        super(InvalidCommentIdError, self).__init__(msg)


class QamInterpreter(cmdln.Cmdln):
    """Usage: osc qam [command] [opts] [args]

    openSUSE build service command-line tool qam extensions.

    ${command_list}
    ${help_list}
    """
    INTERPRETER_QUIT = 3
    SUBQUERY_QUIT = 4

    def __init__(self, parent_cmdln, *args, **kwargs):
        cmdln.Cmdln.__init__(self, *args, **kwargs)
        self.parent_cmdln = parent_cmdln

    name = 'osc qam'
    all_columns_string = ", ".join([str(f) for f in ReportFields.all_fields])
    all_reasons_string = ", ".join([r.flag for r in RejectReason])

    def _set_required_params(self, opts):
        self.parent_cmdln.postoptparse()
        self.apiurl = self.parent_cmdln.get_api_url()
        self.api = RemoteFacade(self.apiurl)
        self.affected_user = None
        if hasattr(opts, 'user') and opts.user:
            self.affected_user = opts.user
        else:
            self.affected_user = osc.conf.get_apiurl_usr(self.apiurl)

    def yes_no(self, question, default = 'no'):
        if default not in ('yes', 'no'):
            raise ValueError("Default must be 'yes' or 'no'")
        valid = {'y': True, 'yes': True,
                 'n': False, 'no': False}
        if default == 'yes':
            default = 'y'
            prompt = '[Y/n]'
        else:
            default = 'n'
            prompt = '[y/N]'
        while True:
            answer = raw_input(' '.join([question, prompt])).lower()
            if not answer:
                return valid[default]
            elif valid.get(answer, None) != None:
                return valid[answer]
            else:
                print("Invalid choice, please use 'yes' or 'no'")

    @cmdln.option('-U',
                  '--user',
                  help = 'User to approve for.')
    @cmdln.option('-G',
                  '--group',
                  help = 'Group to approve for this request.')
    def do_approve(self, subcmd, opts, request_id):
        """${cmd_name}: Approve the request for the user.

        The command either uses the user that runs the osc command or the user
        that was passed as part of the command via the -U flag.

        ${cmd_usage}
        ${cmd_option_list}
        """
        self._set_required_params(opts)
        self.request_id = request_id
        if opts.group:
            action = ApproveGroupAction(self.api, self.affected_user,
                                        self.request_id, opts.group)
        else:
            action = ApproveUserAction(self.api, self.affected_user,
                                       self.request_id, self.affected_user)
        action()

    @cmdln.option('-U',
                  '--user',
                  help = 'User to assign for this request.')
    @cmdln.option('-G',
                  '--group',
                  action = 'append',
                  help = 'Groups to assign the user for.'
                  'Pass multiple groups passing flag multiple times.')
    @cmdln.option('--skip-template',
                  action = 'store_true',
                  default = False,
                  help = 'Will not check if a template exists.')
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
        template_required = False if opts.skip_template else True
        action = AssignAction(self.api, self.affected_user, self.request_id,
                              group, template_required = template_required)
        try:
            action()
        except NotPreviousReviewerError as e:
            print(str(e))
            force = self.yes_no("Do you still want to assign yourself?")
            if not force:
                return
            action = AssignAction(self.api, self.affected_user, self.request_id,
                                  group, force = force)
            action()

    def _list_requests(self, action, tabular, keys):
        """Display the requests from the action.

        :param action: Action that obtains the requests.
        :type action: :class:`oscqam.actions.ListAction`.
        :param tabular: True if output should be formatted in a table.
        :type tabular: bool
        :param keys: The keys to output
        :type keys: [str]
        """
        listdata = action()
        formatter = TabularOutput() if tabular else VerboseOutput()
        if listdata:
            print(formatter.output(keys, listdata))

    @cmdln.option('-G',
                  '--group',
                  action = 'append',
                  default = [],
                  help = 'Only requests containing open reviews for the given '
                  'groups will be output.')
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
        if opts.group:
            action = ListGroupAction(self.api, self.affected_user, opts.group)
        else:
            action = ListOpenAction(self.api, self.affected_user)
        keys = fields.fields(action)
        self._list_requests(action, opts.tabular, keys)

    @cmdln.option('-G',
                  '--group',
                  action = 'append',
                  default = [],
                  help = 'Only requests containing assigned reviews for the  '
                  'given groups will be output.')
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
        if opts.user and opts.group:
            raise ConflictingOptions("Only pass '-U' or '-G' not both")
        self._set_required_params(opts)
        fields = ReportFields.review_fields_by_opts(opts)
        if opts.user:
            action = ListAssignedUserAction(self.api, self.affected_user)
        elif opts.group:
            action = ListAssignedGroupAction(self.api, self.affected_user,
                                             opts.group)
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
    def do_my(self, subcmd, opts):
        """${cmd_name}: Show a list of OBS qam-requests assigned to you.

        ${cmd_usage}
        ${cmd_option_list}
        """
        self._set_required_params(opts)
        opts.user = self.affected_user
        # If we call do_assigned we have to make sure that the optparse.Values
        # instance adheres to the expected interface.
        setattr(opts, 'group', [])
        self.do_assigned(subcmd, opts)

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

    def query_enum(self, enum, id, desc):
        """Query the user to specify one specific option from an enum.

        The enum needs a method 'from_id' that returns the enum for
        the given id.

        :param enum: The enum class to query for

        :param id: Function that returns a unique id for a enum-member.
        :type id: enum -> object

        :param desc: Function that returns a descriptive text
                for a enum-member.
        :type id: enum -> str

        :returns: enum selected by the user.

        """
        ids = [id(member) for member in enum]
        for member in enum:
            print("{0}. {1}".format(id(member), desc(member)))
        print("q. Quit")
        user_input = raw_input("Please specify the options "
                               "(separate multiple values with ,): ")
        if user_input.lower() == 'q':
            return self.SUBQUERY_QUIT
        numbers = map(lambda s: int(s.strip()), user_input.split(','))
        for number in numbers:
            if number not in ids:
                print("Invalid number specified: {0}".format(number))
                return self.query_enum(enum, id, desc)
        return map(enum.from_id, numbers)

    @cmdln.option('-U',
                  '--user',
                  help = 'User that rejects this request.')
    @cmdln.option('-M',
                  '--message',
                  help = 'Message to use for rejection-comment.')
    @cmdln.option('-R',
                  '--reason',
                  action = 'append',
                  help = 'Reason the request was rejected: '
                         + all_reasons_string)
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
        reasons = (map(RejectReason.from_str, opts.reason) if opts.reason
                   else self.query_enum(RejectReason,
                                        lambda r: r.enum_id,
                                        lambda r: r.text))
        if reasons == self.SUBQUERY_QUIT:
            return
        action = RejectAction(self.api, self.affected_user, self.request_id,
                              reasons, message)
        action()

    @cmdln.option('-U',
                  '--user',
                  help = 'User to assign for this request.')
    @cmdln.option('-G',
                  '--group',
                  action = 'append',
                  help = 'Groups to reassign to this request.'
                  'Pass multiple groups passing flag multiple times.')
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

    @cmdln.alias('rmcomment')
    def do_deletecomment(self, subcmd, opts, request_id):
        """${cmd_name}: Remove a comment for the given request.

        The command will list all available comments of the request to allow
        choosing the one to remove.

        ${cmd_usage}
        ${cmd_option_list}
        """
        self._set_required_params(opts)
        request = self.api.requests.by_id(request_id)
        if not request.comments:
            raise NoCommentsError()
        print("CommentID: Message")
        print("------------------")
        for comment in request.comments:
            print("{0}: {1}".format(comment.id, comment.text))
        comment_id = raw_input("Comment-Id to remove: ")
        if comment_id not in [c.id for c in request.comments]:
            raise InvalidCommentIdError(comment_id, request.comments)
        action = DeleteCommentAction(self.api, self.affected_user, comment_id)
        action()

    def do_version(self, subcmd, opts):
        """${cmd_name}: Print the plugin's version."""
        print(strict_version)

    @cmdln.alias('q')
    @cmdln.alias('Q')
    @cmdln.alias('exit')
    def do_quit(self, subcmd, opts):
        """${cmd_name}: Quit the qam-subinterpreter."""
        self.stop = True
        return self.INTERPRETER_QUIT

    def _do_EOF(self, argv):
        cmdln.Cmdln._do_EOF(self, argv)
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
              action = 'append',
              help = 'Define the groups to use for the command.'
              'Pass multiple groups passing flag multiple times.')
@cmdln.option('-M',
              '--message',
              help = 'Message to use for the command.')
@cmdln.option('-R',
              '--reason',
              action = 'append',
              help = 'Reason a request has to be rejected.')
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
@cmdln.option('--skip-template',
              help = 'Will not check if a template exists.')
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
            ret = e.return_code
        finally:
            restore_osc_stdout()
    return ret
