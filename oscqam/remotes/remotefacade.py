"""Provides a facade for interacting with the remote build service."""

import logging
from urllib.error import HTTPError
from urllib.parse import urlencode

import osc.core

from .bugremote import BugRemote
from .commentremote import CommentRemote
from .groupremote import GroupRemote
from .priorityremote import PriorityRemote
from .projectremote import ProjectRemote
from .remoteerror import RemoteError
from .requestremote import RequestRemote
from .userremote import UserRemote


class RemoteFacade:
    """A facade for interacting with the remote build service.

    This class provides a simplified interface to the various remote APIs.

    Attributes:
        remote: The URL of the remote build service.
        comments: A CommentRemote object for interacting with comments.
        groups: A GroupRemote object for interacting with groups.
        requests: A RequestRemote object for interacting with requests.
        users: A UserRemote object for interacting with users.
        projects: A ProjectRemote object for interacting with projects.
        priorities: A PriorityRemote object for interacting with priorities.
        bugs: A BugRemote object for interacting with bugs.
    """

    def __init__(self, remote):
        """Initialize a new RemoteFacade that points to the given remote.

        Args:
            remote: The URL of the remote build service.
        """
        self.remote = remote
        self.comments = CommentRemote(self)
        self.groups = GroupRemote(self)
        self.requests = RequestRemote(self)
        self.users = UserRemote(self)
        self.projects = ProjectRemote(self)
        self.priorities = PriorityRemote(self)
        self.bugs = BugRemote(self)

    def _check_for_error(self, answer):
        """Checks if the response from the remote contains an error.

        Args:
            answer: The response object from the remote.

        Raises:
            RemoteError: If the response contains an error.
        """
        ret_code = answer.status
        if ret_code >= 400 and ret_code < 600:
            raise RemoteError(
                answer.url, ret_code, answer.msg, answer.headers, answer.fp
            )

    def delete(self, endpoint, params=None):
        """Sends a DELETE request to the remote.

        Args:
            endpoint: The API endpoint to send the request to.
            params: A dictionary of parameters to include in the request.

        Returns:
            The XML response from the remote.
        """
        url = "/".join([self.remote, endpoint])
        if params:
            params = urlencode(params)
            url = url + "?" + params
        remote = osc.core.http_DELETE(url)
        self._check_for_error(remote)
        xml = remote.read()
        return xml

    def get(self, endpoint, params=None):
        """Retrieve information at the given endpoint with the parameters.

        Args:
            endpoint: The API endpoint to send the request to.
            params: A dictionary of parameters to include in the request.

        Returns:
            The XML response from the remote.

        Raises:
            RemoteError: If an HTTPError occurs.
        """
        url = "/".join([self.remote, endpoint])
        if params:
            params = urlencode(params)
            url = url + "?" + params
        try:
            logging.debug("Retrieving: %s" % url)
            remote = osc.core.http_GET(url)
        except HTTPError as e:
            raise RemoteError(e.url, e.status, e.msg, e.headers, e.fp)
        self._check_for_error(remote)
        xml = remote.read()
        return xml

    def post(self, endpoint, data=None):
        """Sends a POST request to the remote.

        Args:
            endpoint: The API endpoint to send the request to.
            data: The data to include in the request body.

        Returns:
            The XML response from the remote.

        Raises:
            RemoteError: If an HTTPError occurs.
        """
        url = "/".join([self.remote, endpoint])
        try:
            logging.debug("Posting: %s" % url)
            remote = osc.core.http_POST(url, data=data)
            self._check_for_error(remote)
            xml = remote.read()
            return xml
        except HTTPError as e:
            raise RemoteError(e.url, e.status, e.msg, e.headers, e.fp)
