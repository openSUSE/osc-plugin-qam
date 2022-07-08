from urllib.error import HTTPError
from xml.etree import ElementTree as ET

from ..domains import Priority, UnknownPriority


class PriorityRemote:
    """Get priority information for a request (if available)."""

    endpoint = "/source/{0}/_attribute/OBS:IncidentPriority"

    def __init__(self, remote):
        self.remote = remote

    def _priority(self, request):
        endpoint = self.endpoint.format(request.src_project)
        try:
            xml = ET.fromstring(self.remote.get(endpoint))
        except HTTPError:
            return UnknownPriority()
        else:
            value = xml.find(".//value")
            try:
                return Priority(value.text)
            except AttributeError:
                return UnknownPriority()

    def for_request(self, request):
        return self._priority(request)
