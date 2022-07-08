from ..models import Bug


class BugRemote:
    """Get bug information for a request.

    This loads the patchinfo-file and parses it."""

    endpoint = "/source/{incident}/patchinfo/_patchinfo"

    def __init__(self, remote):
        self.remote = remote

    def for_request(self, request):
        incident = request.src_project
        endpoint = self.endpoint.format(incident=incident)
        xml = self.remote.get(endpoint)
        return Bug.parse(self.remote, xml, "issue")
