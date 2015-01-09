import itertools
import logging
import sys
import urllib2
from osc import cmdln
import osc.commandline
import osc.conf

from oscqam.actions import (ApproveAction, AssignAction, ListAction,
                            UnassignAction, RejectAction, ActionError,
                            CommentAction)
from oscqam.models import RemoteFacade

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def output(template):
    if not template:
        return
    entries = template.log_entries
    print "-----------------------"
    keys = ["ReviewRequestID", "Products", "SRCRPMs", "Bugs", "Category",
            "Rating", "Unassigned Roles", "Assigned Roles", "Package-Streams"]
    length = max([len(k) for k in keys])
    str_template = "{{0:{length}s}}: {{1}}".format(length=length)
    for key in keys:
        try:
            if key == "Unassigned Roles":
                names = [r.name for r in template.request.review_list_open()]
                value = " ".join(names)
            elif key == "Package-Streams":
                packages = [p for p in template.request.packages]
                value = " ".join(packages)
            elif key == "Assigned Roles":
                roles = template.request.assigned_roles
                assigns = ["{r.user} ({r.group})".format(r=r)
                           for r in roles]
                value = ", ".join(assigns)
            else:
                value = entries[key]
            print str_template.format(key, value)
        except KeyError:
            logger.debug("Missing key: %s", key)


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
        except ActionError, e:
            print("Error occurred while performing an action.")
            print(e.msg)
        except urllib2.HTTPError:
            print("Error occurred on the server.")
            print(e.msg)

    @cmdln.option('-U', '--user',
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

    @cmdln.option('-U', '--user',
                  help='User to assign for this request.')
    @cmdln.option('-G', '--group',
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

    @cmdln.option('-U', '--user',
                  help='User to list requests for.')
    @cmdln.option('-R', '--review', action='store_true',
                  help='Show all requests that are in review by the user.')
    def do_list(self, subcmd, opts):
        """${cmd_name}: Show a list of all open requests currently running.
        The list will only contain requests that are part of the qam-groups.

        ${cmd_usage}
        ${cmd_option_list}
        """
        def group_by_rating(template):
            entries = template.log_entries
            rating = entries["Rating"]
            return rating

        def sort_by_rating(template):
            entries = template.log_entries
            rating = entries["Rating"]
            return mapping.get(rating, 10)
        self._set_required_params(opts)
        only_review = opts.review if opts.review else False
        action = ListAction(self.api, self.affected_user, only_review)
        templates = self._run_action(action)
        mapping = {
            'important': 0,
            'moderate': 1,
            'low': 2,
            '': 3
        }
        if templates:
            templates = [t for t in templates if t is not None]
            sort_by_rating = templates.sort(key=sort_by_rating)
            group_rating = itertools.groupby(templates, group_by_rating)
            for key, group in group_rating:
                templates = list(group)
                templates.sort(key=lambda t: int(t.request.reqid))
                # for template in group:
                for template in templates:
                    output(template)

    @cmdln.option('-U', '--user',
                  help='User that rejects this request.')
    @cmdln.option('-M', '--message',
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

    @cmdln.option('-U', '--user',
                  help='User to assign for this request.')
    @cmdln.option('-G', '--group',
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


@cmdln.option('-G', '--group',
              help='Group to use for the command.')
@cmdln.option('-M', '--message',
              help='Message to use for the command.')
@cmdln.option('-R', '--review', action='store_true',
              help='Parameter for list command.')
@cmdln.option('-U', '--user',
              help='User to use for the command.')
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
