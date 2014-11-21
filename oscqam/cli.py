import sys

from osc import cmdln
import osc.conf

from oscqam.actions import (ApproveAction, AssignAction, ListAction,
                            UnassignAction, RejectAction)
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


class QamInterpreter(cmdln.Cmdln):
    def _set_required_params(self, opts):
        self.apiurl = osc.conf.config['apiurl']
        self.api = RemoteFacade(self.apiurl)
        self.affected_user = None
        if opts.user:
            self.affected_user = opts.user
        else:
            self.affected_user = osc.conf.get_apiurl_usr(self.apiurl)

    @cmdln.option('-u', '--user',
                  help='User to assign for this request.')
    def do_approve(self, subcmd, opts, request_id):
        self._set_required_params(opts)
        self.request_id = request_id
        action = ApproveAction(self.api, self.affected_user, self.request_id)
        success = action()

    @cmdln.option('-u', '--user',
                  help='User to assign for this request.')
    def do_assign(self, subcmd, opts, request_id):
        """${cmd_name}: Assign the configured (or passed user) to the request.

        """
        self._set_required_params(opts)
        self.request_id = request_id
        action = AssignAction(self.api, self.affected_user, self.request_id)
        success = action()

    @cmdln.option('-u', '--user',
                  help='User to assign for this request.')
    def do_list(self, subcmd, opts):
        """${cmd_name}: Show a list of all open requests currently running.
        The command either uses the configured user or the user passed via
        the `-u` flag.

        """
        # Products: DESKTOP 12 (x86_64), SDK 12 (x86_64, s390x, ppc64le), WE 12 (x86_64)               <--- from template, remove SLE-
        # Sources: webkitgtk, webkitgtk3                                                               <--- from template
        # Bugs: 899922                                                                                 <--- from template
        # Category: recommended                                                                        <--- from template
        # Rating: important                                                                            <--- from template
        # Coordinator: "Leonardo Chiquitto" <lchiquitto@suse.com>                                      <--- from template
        self._set_required_params(opts)
        action = ListAction(self.api, self.affected_user)
        templates = action()
        for template in templates:
            output(template)
        return

    @cmdln.option('-u', '--user',
                  help='User to assign for this request.')
    def do_reject(self, subcmd, opts, request_id):
        self._set_required_params(opts)
        self.request_id = request_id
        action = RejectAction(self.api, self.affected_user, self.request_id)
        success = action()

    @cmdln.option('-u', '--user',
                  help='User to assign for this request.')
    def do_unassign(self, subcmd, opts, request_id):
        """${cmd_name}: Assign the configured (or passed user) to the request.

        """
        self._set_required_params(opts)
        self.request_id = request_id
        action = UnassignAction(self.api, self.affected_user, self.request_id)
        success = action()

def do_qam(self, subcmd, opts, arg=None):
    """Start the QA-Maintenance specific submode of osc for request handling.
    """
    osc.conf.get_config()
    interp = QamInterpreter()
    interp.optparser = cmdln.SubCmdOptionParser()
    if arg:
        return interp.main()
    else:
        interp.cmdloop()
        
    
