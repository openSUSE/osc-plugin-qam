"""Provides a class for interacting with bugs on the remote."""

from ..models import Bug


class BugRemote:
    """Get bug information for a request.

    This loads the patchinfo-file and parses it.

    Attributes:
        endpoint: The API endpoint for getting patch information.
        remote: A remote facade.
    """

    endpoint = "/source/{incident}/patchinfo/_patchinfo"

    def __init__(self, remote):
        """Initializes a BugRemote.

        Args:
            remote: A remote facade.
        """
        self.remote = remote

    def for_request(self, request):
        """Gets the bugs for a given request.

        Args:
            request: The request to get bugs for.

        Returns:
            A list of Bug objects.
        """
        if request.src_project.startswith("SUSE:SLFO:"):
            return []
        incident = request.src_project
        endpoint = self.endpoint.format(incident=incident)
        xml = self.remote.get(endpoint)
        return Bug.parse(self.remote, xml, "issue")
