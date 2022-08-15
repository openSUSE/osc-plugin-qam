from urllib.error import HTTPError
from xml.etree import ElementTree as ET

import requests
import urllib3
import urllib3.exceptions

from ..domains import Priority, UnknownPriority

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PriorityRemote:
    """Get priority information for a request (if available)."""

    endpoint = "/source/{0}/_attribute/OBS:IncidentPriority"
    smelt = "http://smelt.suse.de/graphql"
    query = "{{ incidents(incidentId: {incident}) {{ edges {{ node {{ priority priorityOverride }} }} }} }}"

    def __init__(self, remote):
        self.remote = remote

    def _priority(self, request):
        endpoint = self.endpoint.format(request.src_project)
        try:
            xml = ET.fromstring(self.remote.get(endpoint))
        except HTTPError:
            return self._smelt_prio(request)
        else:
            value = xml.find(".//value")
            try:
                if value is not None:
                    return Priority(value.text)
                else:
                    return self._smelt_prio(request)
            except AttributeError:
                return self._smelt_prio(request)

    def _smelt_prio(self, request):
        try:
            prio = requests.get(
                self.smelt,
                params={"query": self.query.format(incident=request.incident)},
                verify=False,
            ).json()
            prio = prio["data"]["incidents"].get("edges", None)
            if not prio:
                return UnknownPriority()
            return Priority(prio[0]["node"]["priority"])
        except Exception:
            return UnknownPriority()

    def for_request(self, request):
        return self._priority(request)
