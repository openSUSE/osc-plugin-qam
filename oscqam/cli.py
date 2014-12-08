import sys
from osc import cmdln
import osc.conf

from oscqam.actions import (ApproveAction, AssignAction, ListAction,
                            UnassignAction, RejectAction, ActionError)
from oscqam.models import RemoteFacade


def output(template):
    if not template:
        return
    print
    print "-----------------------"
    entries = template.log_entries
    keys = ["ReviewRequestID", "Products", "SRCRPMs", "Bugs", "Category",
            "Rating"]
    for key in keys:
        print "{0}: {1}".format(key, entries[key])
    names = [r.name for r in template.request.review_list_open()]
    print "Unassigned Roles: {0}".format(names)
    print "Origin: {0}".format(template.request.origin)


class QamInterpreter(cmdln.Cmdln):
    """Usage: osc qam [command] [opts] [args]

    openSUSE build service command-line tool qam extensions.

    ${command_list}
    ${help_list}
    """
    name = 'osc-qam'

    def _set_required_params(self, opts):
        self.apiurl = osc.conf.config['apiurl']
        self.api = RemoteFacade(self.apiurl)
        self.affected_user = None
        if opts.user:
            self.affected_user = opts.user
        else:
            self.affected_user = osc.conf.get_apiurl_usr(self.apiurl)

    def _run_action(self, func):
        """Run the given action and catch (expected) errors that might occur.

        """
        try:
            return func()
        except ActionError, e:
            print("Error occurred while performing an action.")
            print(e.msg)

    @cmdln.option('-u', '--user',
                  help='User to assign for this request.')
    def do_approve(self, subcmd, opts, request_id):
        """${cmd_name}: Approve the request for the user.

        The command either uses the user that runs the osc command or the user
        that was passed as part of the command via the -u flag.

        ${cmd_usage}
        ${cmd_option_list}
        """
        self._set_required_params(opts)
        self.request_id = request_id
        action = ApproveAction(self.api, self.affected_user, self.request_id)
        self._run_action(action)

    @cmdln.option('-u', '--user',
                  help='User to assign for this request.')
    @cmdln.option('-g', '--group',
                  help='Group to assign the user for.')
    def do_assign(self, subcmd, opts, request_id):
        """${cmd_name}: Assign the request to the user.

        The command either uses the user that runs the osc command or the user
        that was passed as part of the command via the -u flag.

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

    @cmdln.option('-u', '--user',
                  help='User to list requests for.')
    @cmdln.option('-r', '--review', action='store_true',
                  help='Show all requests that are in review by the user.')
    def do_list(self, subcmd, opts):
        """${cmd_name}: Show a list of all open requests currently running.
        The list will only contain requests that are part of the qam-groups.

        ${cmd_usage}
        ${cmd_option_list}
        """
        self._set_required_params(opts)
        only_review = opts.review if opts.review else False
        action = ListAction(self.api, self.affected_user, only_review)
        templates = self._run_action(action)
        if templates:
            for template in templates:
                output(template)

    @cmdln.option('-u', '--user',
                  help='User that rejects this request.')
    @cmdln.option('-m', '--message',
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

    @cmdln.option('-u', '--user',
                  help='User to assign for this request.')
    @cmdln.option('-g', '--group',
                  help='Group to reassign to this request.')
    def do_unassign(self, subcmd, opts, request_id):
        """${cmd_name}: Assign the request to the user.

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

    @cmdln.alias('q')
    def do_quit(self, subcmd, opts):
        """${cmd_name}: Quit the qam-subinterpreter."""
        self.stop = True


@cmdln.option('-g', '--group',
              help='Group to use for the command.')
@cmdln.option('-m', '--message',
              help='Message to use for the command.')
@cmdln.option('-r', '--review', action='store_true',
              help='Parameter for list command.')
@cmdln.option('-u', '--user',
              help='User to use for the command.')
def do_qam(self, subcmd, opts, *args, **kwargs):
    """Start the QA-Maintenance specific submode of osc for request handling.
    """
    osc.conf.get_config()
    interp = QamInterpreter()
    interp.optparser = cmdln.SubCmdOptionParser()
    if args:
        return interp.onecmd(sys.argv[3:])
    else:
        return interp.cmdloop()
