"""Provides a class for interacting with incident priorities on the remote."""

from urllib.error import HTTPError
from xml.etree import ElementTree as ET

import requests
import urllib3
import urllib3.exceptions

from ..domains import Priority, UnknownPriority

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PriorityRemote:
    """Get priority information for a request (if available).

    Attributes:
        endpoint: The API endpoint for getting incident priority.
        smelt: The URL for the smelt GraphQL API.
        query: The GraphQL query for getting incident priority from smelt.
        remote: A remote facade.
    """

    endpoint = "/source/{0}/_attribute/OBS:IncidentPriority"
    smelt = "http://smelt.suse.de/graphql"
    query = "{{ incidents(incidentId: {incident}) {{ edges {{ node {{ priority priorityOverride }} }} }} }}"

    def __init__(self, remote):
        """Initializes a PriorityRemote.

        Args:
            remote: A remote facade.
        """
        self.remote = remote

    def _priority(self, request):
        """Gets the priority for a given request.

        It first tries to get the priority from the build service attribute.
        If that fails, it falls back to getting it from smelt.

        Args:
            request: The request to get the priority for.

        Returns:
            A Priority object.
        """
        endpoint = self.endpoint.format(request.src_project)
        try:
            xml = ET.fromstring(self.remote.get(endpoint))
        except HTTPError:
            return self._smelt_prio(request)
        else:
            value = xml.find(".//value")
            try:
                return Priority(value.text)
            except (AttributeError, TypeError):
                return self._smelt_prio(request)

    def _smelt_prio(self, request):
        """Gets the priority for a given request from smelt.

        Args:
            request: The request to get the priority for.

        Returns:
            A Priority object, or UnknownPriority if it cannot be determined.
        """
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
        """Gets the priority for a given request.

        Args:
            request: The request to get the priority for.

        Returns:
            A Priority object.
        """
        return self._priority(request)
