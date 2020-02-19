import logging
from xml.etree import cElementTree as ET

import osc

from .domains import Priority, UnknownPriority
from .errors import ReportedError
from .models import Attribute, Comment, Group, Request, User, RequestFilter, Bug
from .utils import memoize

from urllib.parse import urlencode
from urllib.error import HTTPError


class RemoteError(ReportedError):
    """Indicates an error while communicating with the remote service.

    """
    _msg = "Error accessing {url} - {ret_code}: {msg}"

    def __init__(self, url, ret_code, msg, headers, fp):
        self.url = url
        self.ret_code = ret_code
        self.msg = msg
        self.headers = headers
        self.fp = fp
        super().__init__(self._msg.format(
            url=self.url,
            ret_code=self.ret_code,
            msg=self.msg)
                                          )


class RemoteFacade:
    def __init__(self, remote):
        """Initialize a new RemoteOscRemote that points to the given remote.
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
        ret_code = answer.getcode()
        if ret_code >= 400 and ret_code < 600:
            raise RemoteError(answer.url, ret_code, answer.msg,
                              answer.headers, answer.fp)

    def delete(self, endpoint, params = None):
        url = '/'.join([self.remote, endpoint])
        if params:
            params = urlencode(params)
            url = url + "?" + params
        remote = osc.core.http_DELETE(url)
        self._check_for_error(remote)
        xml = remote.read()
        return xml

    def get(self, endpoint, params = None):
        """Retrieve information at the given endpoint with the parameters.

        Call the callback function with the result.

        """
        url = '/'.join([self.remote, endpoint])
        if params:
            params = urlencode(params)
            url = url + "?" + params
        try:
            logging.debug(f"Retrieving: {url}")
            remote = osc.core.http_GET(url)
        except HTTPError as e:
            raise RemoteError(e.url, e.getcode(), e.msg, e.headers, e.fp)
        self._check_for_error(remote)
        xml = remote.read()
        return xml

    def post(self, endpoint, data = None):
        url = '/'.join([self.remote, endpoint])
        try:
            logging.debug(f"Posting: {url}")
            remote = osc.core.http_POST(url, data = data)
            self._check_for_error(remote)
            xml = remote.read()
            return xml
        except HTTPError as e:
            raise RemoteError(e.url, e.getcode(), e.msg, e.headers, e.fp)


class RequestRemote():
    """Facade for retrieving Request objects from the buildservice API.
    """
    def __init__(self, remote):
        self.remote = remote
        self.endpoint = 'request'

    def _group_xpath(self, groups, state):
        """Search the given groups with the given state.
        """
        def get_group_name(group):
            if isinstance(group, str):
                return group
            return group.name
        xpaths = []
        for group in groups:
            name = get_group_name(group)
            xpaths.append(
                "(review[@by_group='{0}' and @state='{1}'])".format(name,
                                                                    state)
            )
        xpath = " or ".join(xpaths)
        return "( {0} )".format(xpath)

    def _get_groups(self, groups, state, **kwargs):
        if not kwargs:
            kwargs = {'withfullhistory': '1'}
        xpaths = ["(state/@name='{0}')".format('review')]
        xpaths.append(self._group_xpath(groups, state))
        xpath = " and ".join(xpaths)
        params = {'match': xpath,
                  'withfullhistory': '1'}
        params.update(kwargs)
        search = "/".join(["search", self.endpoint])
        requests = Request.parse(self.remote, self.remote.get(search, params))
        return RequestFilter.for_remote(
            self.remote
        ).maintenance_requests(requests)

    def open_for_groups(self, groups, **kwargs):
        """Will return all requests of the given type for the given groups
        that are still open: the state of the review should be in state 'new'.

        Args:
            - remote: The remote facade to use.
            - groups: The groups that should be used.
            - **kwargs: additional parameters for the search.
        """
        return self._get_groups(groups, 'new', **kwargs)

    def review_for_groups(self, groups, **kwargs):
        """Will return all requests for the given groups that are in review.

        As there is no 'review' state, the state is determined as a group being
        'accepted', while a user is in state 'new' for that group.

        Args:
            - remote: The remote facade to use.
            - groups: The groups that should be used.
            - **kwargs: additional parameters for the search.
        """
        requests = self._get_groups(groups, 'accepted', **kwargs)
        return [request for request in requests if request.assigned_roles]

    def for_user(self, user):
        """Will return all requests for the user if they are part of a
        SUSE:Maintenance project.

        """
        params = {'user': user.login,
                  'view': 'collection',
                  'states': 'new,review',
                  'withfullhistory': '1'}
        requests = Request.parse(self.remote,
                                 self.remote.get(self.endpoint, params))
        return RequestFilter.for_remote(
            self.remote
        ).maintenance_requests(requests)

    def for_incident(self, incident):
        """Return all requests for the given incident that have a qam-group
        as reviewer.
        """
        params = {'project': incident,
                  'view': 'collection',
                  'withfullhistory': '1'}
        requests = Request.parse(self.remote,
                                 self.remote.get(self.endpoint, params))
        return [request for request in requests
                if any([r.reviewer.is_qam_group()
                        for r in request.review_list()])]

    def by_id(self, req_id):
        req_id = Request.parse_request_id(req_id)
        endpoint = "/".join([self.endpoint, req_id])
        req = Request.parse(self.remote, self.remote.get(
            endpoint,
            {'withfullhistory': 1}
        ))
        return req[0]


class GroupRemote:
    def __init__(self, remote):
        self.remote = remote
        self.endpoint = 'group'

    @memoize
    def all(self):
        group_entries = Group.parse_entry(self.remote,
                                          self.remote.get(self.endpoint))
        return group_entries

    def for_pattern(self, pattern):
        return [group for group in self.all()
                if pattern.match(group.name)]

    @memoize
    def for_name(self, group_name):
        url = '/'.join([self.endpoint, group_name])
        group = Group.parse(self.remote, self.remote.get(url))
        if group:
            return group[0]
        else:
            raise AttributeError(
                "No group found for name: {0}".format(
                    group_name
                )
            )

    @memoize
    def for_user(self, user):
        params = {'login': user.login}
        group_entries = Group.parse_entry(self.remote,
                                          self.remote.get(self.endpoint,
                                                          params))
        groups = [self.for_name(g.name) for g in group_entries]
        return groups


class UserRemote:
    def __init__(self, remote):
        self.remote = remote
        self.endpoint = 'person'

    @memoize
    def by_name(self, name):
        url = '/'.join([self.endpoint, name])
        users = User.parse(self.remote, self.remote.get(url))
        if users:
            return users[0]
        raise AttributeError("User not found.")


class CommentRemote:
    endpoint = 'comments'
    delete_endpoint = 'comment'

    def __init__(self, remote):
        self.remote = remote

    def for_request(self, request):
        endpoint = '{0}/request/{1}'.format(self.endpoint, request.reqid)
        xml = self.remote.get(endpoint)
        return Comment.parse(self.remote, xml)

    def delete(self, comment_id):
        endpoint = '{0}/{1}'.format(self.delete_endpoint, comment_id)
        self.remote.delete(endpoint)


class ProjectRemote:
    create_body = """<attributes>
    {attribute}
    </attributes>
    """

    endpoint = 'source'

    def __init__(self, remote):
        self.remote = remote

    def get_attribute(self, project, attribute_name):
        """Return the attribute value for the given project."""
        url = "{endpoint}/{project}/_attribute/{attrib}".format(
            endpoint = self.endpoint,
            project = project,
            attrib = attribute_name
        )
        return Attribute.parse(self.remote,
                               self.remote.get(url))

    def set_attribute(self, project, attribute):
        endpoint = '{0}/{1}/_attribute/{2}:{3}'.format(self.endpoint,
                                                       project,
                                                       attribute.namespace,
                                                       attribute.name)
        self.remote.post(endpoint,
                         self.create_body.format(attribute = attribute.xml()))


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
        return Bug.parse(self.remote, xml, 'issue')
