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
    def __init__(self, remote):
        """Initialize a new RemoteOscRemote that points to the given remote."""
        self.remote = remote
        self.comments = CommentRemote(self)
        self.groups = GroupRemote(self)
        self.requests = RequestRemote(self)
        self.users = UserRemote(self)
        self.projects = ProjectRemote(self)
        self.priorities = PriorityRemote(self)
        self.bugs = BugRemote(self)

    def _check_for_error(self, answer):
        ret_code = answer.status
        if ret_code >= 400 and ret_code < 600:
            raise RemoteError(
                answer.url, ret_code, answer.msg, answer.headers, answer.fp
            )

    def delete(self, endpoint, params=None):
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

        Call the callback function with the result.

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
        url = "/".join([self.remote, endpoint])
        try:
            logging.debug("Posting: %s" % url)
            remote = osc.core.http_POST(url, data=data)
            self._check_for_error(remote)
            xml = remote.read()
            return xml
        except HTTPError as e:
            raise RemoteError(e.url, e.status, e.msg, e.headers, e.fp)
