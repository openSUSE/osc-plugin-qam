import sys

from osc import cmdln
import osc.conf

from osc_qam_plugin.actions import RequestAction
from osc_qam_plugin.models import RemoteFacade


class QamInterpreter(cmdln.Cmdln):

    def _set_required_params(self, opts):
        self.apiurl = osc.conf.config['apiurl']
        self.api = RemoteFacade(self.apiurl)
        self.affected_user = None
        self.request_id = None
        if opts.user:
            self.affected_user = opts.user
        else:
            self.affected_user = osc.conf.get_apiurl_usr(self.apiurl)

    @cmdln.option('-u', '--user',
                  help='User to assign for this request.')
    def do_list(self, subcmd, opts):
        """${cmd_name}: Show a list of all open requests currently running.
        The command either uses the configured user or the user passed via
        the `-u` flag.

        """
        self._set_required_params(opts)
        action = RequestAction(self.api, self.affected_user,
                               self.request_id)
        return action.list()

    @cmdln.option('-r', '--request',
                  help='Request-id of the request to use in the process.')
    @cmdln.option('-u', '--user',
                  help='User to assign for this request.')
    def do_assign(self, subcmd, opts):
        """${cmd_name}: Assign the configured (or passed user) to the request.

        """
        self._set_required_params(opts)
        pass

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
               
    
