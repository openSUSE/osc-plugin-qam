"""This module contains all models that are required by the QAM plugin to keep
everything in a consistent state.

"""
import contextlib
from functools import total_ordering
import logging
import re
import urllib
import urllib2
try:
    from xml.etree import cElementTree as ET
except ImportError:
    import cElementTree as ET
import osc.core
import osc.oscerr
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def et_iter(elementtree, tag):
    """This function is used to make the iter call work in
    version < 2.7 as well.
    """
    if hasattr(elementtree, 'iter'):
        return elementtree.iter(tag)
    else:
        return elementtree.getiterator(tag)


class ReportedError(RuntimeError):
    """Raise on exceptions that can only be reported but not handled."""


class InvalidRequestError(ReportedError):
    """Raise when a request object is missing required information."""
    def __init__(self, request):
        super(InvalidRequestError, self).__init__(
            "Invalid build service request: {0}".format(request)
        )


class MissingSourceProjectError(InvalidRequestError):
    """Raise when a request is missing the source project property."""
    def __init__(self, request):
        super(MissingSourceProjectError, self).__init__(
            "Invalid build service request: "
            "{0} has no source project.".format(request)
        )


class TemplateNotFoundError(ReportedError):
    """Raise when a template could not be found."""
    def __init__(self, message):
        super(TemplateNotFoundError, self).__init__(
            "Report could not be loaded: {0}".format(message)
        )


class RemoteError(Exception):
    """Indicates an error while communicating with the remote service.

    """
    def __init__(self, url, ret_code, msg, headers, fp):
        self.url = url
        self.ret_code = ret_code
        self.msg = msg
        self.headers = headers
        self.fp = fp


class RemoteFacade(object):
    def __init__(self, remote):
        """Initialize a new RemoteOscRemote that points to the given remote.
        """
        self.remote = remote

    def _check_for_error(self, answer):
        ret_code = answer.getcode()
        if ret_code >= 400 and ret_code < 600:
            raise urllib2.HTTPError(answer.url, ret_code, answer.msg,
                                    answer.headers, answer.fp)

    def get(self, endpoint, params = None):
        """Retrieve information at the given endpoint with the parameters.

        Call the callback function with the result.

        """
        url = '/'.join([self.remote, endpoint])
        if params:
            params = urllib.urlencode(params)
            url = url + "?" + params
        remote = osc.core.http_GET(url)
        self._check_for_error(remote)
        xml = remote.read()
        return xml

    def post(self, endpoint, data = None):
        url = '/'.join([self.remote, endpoint])
        remote = osc.core.http_POST(url, data = data)
        self._check_for_error(remote)
        xml = remote.read()
        return xml


class XmlFactoryMixin(object):
    """Can generate an object from xml by recursively parsing the structure.

    It will set properties to the text-property of a node if there are no
    children.

    Otherwise it will parse the children into another node and set the property
    to a list of these new parsed nodes.
    """
    def __init__(self, remote, attributes, children):
        """Will set every element in kwargs to a property of the class.
        """
        attributes.update(children)
        for kwarg in attributes:
            setattr(self, kwarg, attributes[kwarg])

    @staticmethod
    def listify(dictionary, key):
        """Will wrap an existing dictionary key in a list.
        """
        if not isinstance(dictionary[key], list):
            value = dictionary[key]
            del dictionary[key]
            dictionary[key] = [value]

    @classmethod
    def parse_et(cls, remote, et, tag, wrapper_cls = None):
        """Recursively parses an element-tree instance.

        Will iterate over the tag as root-level.
        """
        if not wrapper_cls:
            wrapper_cls = cls
        objects = []
        for request in et_iter(et, tag):
            attribs = {}
            for attribute in request.attrib:
                attribs[attribute] = request.attrib[attribute]
            kwargs = {}
            for child in request:
                key = child.tag
                subchildren = list(child)
                if subchildren or child.attrib:
                    # Prevent that all children have the same class as the
                    # parent.  This might lead to providing methods that make
                    # no sense.
                    value = cls.parse_et(remote, child, key, XmlFactoryMixin)
                    if len(value) == 1:
                        value = value[0]
                else:
                    if child.text:
                        value = child.text.strip()
                    else:
                        value = None
                if key in kwargs:
                    XmlFactoryMixin.listify(kwargs, key)
                    kwargs[key].append(value)
                else:
                    kwargs[key] = value
            kwargs.update(attribs)
            objects.append(wrapper_cls(remote, attribs, kwargs))
        return objects

    @classmethod
    def parse(cls, remote, xml, tag):
        root = ET.fromstring(xml)
        return cls.parse_et(remote, root, tag, cls)


class Group(XmlFactoryMixin):
    """A group object from the build service.
    """
    endpoint = 'group'

    def __init__(self, remote, attributes, children):
        super(Group, self).__init__(remote, attributes, children)
        self.remote = remote
        if 'title' in children:
            # We set name to title to ensure equality.  This allows us to
            # prevent having to query *all* groups we need via this method,
            # which could use very many requests.
            self.name = children['title']

    @classmethod
    def all(cls, remote):
        group_entries = Group.parse(remote, remote.get(cls.endpoint))
        groups = [Group.for_name(remote, g.name) for g in group_entries]
        return groups

    @classmethod
    def for_name(cls, remote, group_name):
        url = '/'.join([Group.endpoint, group_name])
        group = Group.parse(remote, remote.get(url))
        if group:
            return group[0]
        else:
            raise AttributeError(
                "No group found for name: {0}".format(
                    group_name
                )
            )

    @classmethod
    def for_user(cls, remote, user):
        params = {'login': user.login}
        group_entries = Group.parse_entry(remote, remote.get(cls.endpoint,
                                                             params))
        groups = [Group.for_name(remote, g.name) for g in group_entries]
        return groups

    @classmethod
    def parse(cls, remote, xml):
        return super(Group, cls).parse(remote, xml, 'group')

    @classmethod
    def parse_entry(cls, remote, xml):
        return super(Group, cls).parse(remote, xml, 'entry')

    def __hash__(self):
        # We don't want to hash to the same as only the string.
        return hash(self.name) + hash(type(self))

    def __eq__(self, other):
        return self.name == other.name

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"{0}".format(self.name)


class User(XmlFactoryMixin):
    """Wraps a user of the obs in an object.

    """
    endpoint = 'person'
    QAM_SRE = re.compile(".*qam.*")

    def __init__(self, remote, attributes, children):
        super(User, self).__init__(remote, attributes, children)
        self.remote = remote
        self._groups = None

    @property
    def groups(self):
        """Read-only property for groups a user is part of.
        """
        # Maybe use a invalidating cache as a trade-off between current
        # information and slow response.
        if not self._groups:
            self._groups = Group.for_user(self.remote, self)
        return self._groups

    @property
    def qam_groups(self):
        """Return only the groups that are part of the qam-workflow."""
        return [group for group in self.groups
                if User.QAM_SRE.match(group.name)]

    def __hash__(self):
        return hash(self.login)

    def __eq__(self, other):
        return isinstance(other, User) and self.login == other.login

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return u"{0} ({1})".format(self.realname, self.email)

    @classmethod
    def by_name(cls, remote, name):
        url = '/'.join([User.endpoint, name])
        users = User.parse(remote, remote.get(url))
        if users:
            return users[0]
        raise AttributeError("User not found.")

    @classmethod
    def parse(cls, remote, xml):
        return super(User, cls).parse(remote, xml, cls.endpoint)


class Request(osc.core.Request, XmlFactoryMixin):
    """Wrapper around osc request object to add logic required by the
    qam-plugin.
    """
    @total_ordering
    class Priority(object):
        """Store the priority of this request's associated incident.
        """
        def __init__(self, prio):
            self.priority = int(prio)

        def __eq__(self, other):
            return self.priority == other.priority

        def __lt__(self, other):
            return (self.priority > other.priority)

        def __str__(self):
            return "{0}".format(self.priority)

    class UnknownPriority(Priority):
        def __init__(self):
            self.priority = None

        def __eq__(self, other):
            return isinstance(other, Request.UnknownPriority)

        def __lt__(self, other):
            return False

    class Assignment(object):
        """Minimal class to store an assignment of a user for a group.
        """
        def __init__(self, user, group):
            self.user = user
            self.group = group

        def __hash__(self):
            return hash(self.user) + hash(self.group)

        def __eq__(self, other):
            return (self.user == other.user and
                    self.group == other.group)

        def __str__(self):
            return unicode(self).encode('utf-8')

        def __unicode__(self):
            return u"{1} -> {0}".format(self.user, self.group)

    endpoint = 'request'

    OPEN_STATES = ['new', 'review']
    REVIEW_USER = 'BY_USER'
    REVIEW_GROUP = 'BY_GROUP'
    REVIEW_OTHER = 'BY_OTHER'
    COMPLETE_REQUEST_ID_SRE = re.compile("SUSE:Maintenance:\d+:(?P<req>\d+)")

    def __init__(self, remote):
        self.remote = remote
        super(Request, self).__init__()
        self._groups = None
        self._packages = None
        self._assigned_roles = None
        self._priority = None

    @property
    def incident_priority(self):
        if not self._priority:
            endpoint = "/source/{0}/_attribute/OBS:IncidentPriority".format(
                self.src_project
            )
            try:
                xml = ET.fromstring(self.remote.get(endpoint))
            except urllib2.HTTPError:
                logger.error("Priority not found: %s", endpoint)
                self._priority = self.UnknownPriority()
            else:
                value = xml.find(".//value")
                try:
                    self._priority = self.Priority(value.text)
                except AttributeError:
                    self._priority = self.UnknownPriority()
        return self._priority

    @property
    def assigned_roles(self):
        if not self._assigned_roles:
            self._assigned_roles = self._infer_assignment()
        return self._assigned_roles

    @property
    def groups(self):
        # Maybe use a invalidating cache as a trade-off between current
        # information and slow response.
        return [review.by_group for review in self.reviews if review.by_group]

    @property
    def packages(self):
        """Collects all packages of the actions that are part of the request.
        """
        if not self._packages:
            packages = set()
            for action in self.actions:
                pkg = action.src_package
                if pkg != "patchinfo":
                    packages.add(pkg)
            self._packages = packages
        return self._packages

    @property
    def src_project(self):
        """Will return the src_project or an empty string if no src_project
        can be found in the request.

        """
        for action in self.actions:
            if hasattr(action, 'src_project'):
                prj = action.src_project
                if prj:
                    return prj
                else:
                    logger.info("This project has no source project: %s",
                                self.reqid)
                    return ''
        return ''

    def review_action(self, params, user = None, group = None, comment = None):
        if not user and not group:
            raise AttributeError("group or user required for this action.")
        if user:
            params['by_user'] = user.login
        if group:
            params['by_group'] = group.name
        url_params = urllib.urlencode(params)
        url = "/".join([Request.endpoint, self.reqid])
        url += "?" + url_params
        self.remote.post(url, comment)

    def review_assign(self, group, reviewer, comment = None):
        params = {'cmd': 'assignreview',
                  'reviewer': reviewer.login}
        self.review_action(params, group = group, comment = comment)

    def review_accept(self, user = None, group = None, comment = None):
        comment = "[qamosc]::accept::{user}::{group}".format(
            user = user, group = group
        )
        params = {'cmd': 'changereviewstate',
                  'newstate': 'accepted'}
        self.review_action(params, user, group, comment)

    def review_add(self, user = None, group = None, comment = None):
        """Will add a new reviewrequest for the given user or group.

        """
        params = {'cmd': 'addreview'}
        self.review_action(params, user, group, comment)

    def review_decline(self, user = None, group = None, comment = None):
        """Will decline the reviewrequest for the given user or group.

        """
        params = {'cmd': 'changereviewstate',
                  'newstate': 'declined'}
        self.review_action(params, user, group, comment)

    def review_reopen(self, user = None, group = None, comment = None):
        """Will reopen a reviewrequest for the given user or group.

        """
        params = {'cmd': 'changereviewstate',
                  'newstate': 'new'}
        self.review_action(params, user, group, comment)

    def review_list(self):
        """Returns all reviews as a list.
        """
        def set_name_review(r):
            if r.by_group is not None:
                r.name = r.by_group
                r.review_type = Request.REVIEW_GROUP
            elif r.by_user is not None:
                r.name = r.by_user
                r.review_type = Request.REVIEW_USER
            elif r.who:
                r.name = r.who
                r.review_type = Request.REVIEW_OTHER
            else:
                r.name = ''
                r.review_type = Request.REVIEW_OTHER
        if not self.reviews:
            return []
        if isinstance(self.reviews, list):
            for r in self.reviews:
                set_name_review(r)
            reviews = self.reviews
        else:
            set_name_review(self.review)
            reviews = [self.review]
        return reviews

    def review_list_open(self):
        """Return only open reviews.
        """
        return [r for r in self.review_list() if r.state in
                Request.OPEN_STATES]

    def review_list_accepted(self):
        return [r for r in self.review_list()
                if r.state.lower() == 'accepted']

    def add_comment(self, comment):
        """Adds a comment to this request.
        """
        endpoint = '/comments/request/{id}'.format(id = self.reqid)
        self.remote.post(endpoint, comment)

    def get_template(self, template_factory):
        """Return the template associated with this request.
        """
        if not self.src_project:
            raise MissingSourceProjectError(self)
        return template_factory(self)

    @classmethod
    def filter_by_project(cls, request_substring, requests):
        requests = [r for r in requests if request_substring in r.src_project]
        return requests

    @classmethod
    def for_user(cls, remote, user):
        """Will return all requests for the user if they are part of a
        SUSE:Maintenance project.

        """
        params = {'user': user.login,
                  'view': 'collection',
                  'states': 'new,review',
                  'withfullhistory': '1'}
        requests = cls.parse(remote, remote.get(cls.endpoint, params))
        return cls.filter_by_project("SUSE:Maintenance", requests)

    @classmethod
    def open_for_groups(cls, remote, groups, **kwargs):
        """Will return all requests of the given type for the given groups
        that are still open: the state of the review should be in state 'new'.

        Args:
            - remote: The remote facade to use.
            - groups: The groups that should be used.
            - **kwargs: additional parameters for the search.
        """
        def get_group_name(group):
            if isinstance(group, str):
                return group
            return group.name
        if not kwargs:
            kwargs = {'withfullhistory': '1'}
        xpaths = ["(state/@name = '{0}')".format('review')]
        for group in groups:
            name = get_group_name(group)
            xpaths.append(
                "(review[@by_group = '{0}' and @state = 'new'])".format(name)
            )
        xpath = " and ".join(xpaths)
        params = {'match': xpath,
                  'withfullhistory': '1'}
        params.update(kwargs)
        search = "/".join(["search", cls.endpoint])
        requests = cls.parse(remote, remote.get(search, params))
        return cls.filter_by_project("SUSE:Maintenance", requests)

    @classmethod
    def by_id(cls, remote, req_id):
        req_id = cls.parse_request_id(req_id)
        endpoint = "/".join([cls.endpoint, req_id])
        req = cls.parse(remote, remote.get(endpoint, {'withfullhistory': 1}))
        return req[0]

    @classmethod
    def parse(cls, remote, xml):
        et = ET.fromstring(xml)
        requests = []
        for request in et_iter(et, cls.endpoint):
            try:
                req = Request(remote)
                req.read(request)
                requests.append(req)
            except osc.oscerr.APIError, e:
                logger.error(e.msg)
                pass
        return requests

    @classmethod
    def parse_request_id(cls, request_id):
        """Extract the request_id from a string if required.

        The method will extract the request-id of a complete request string
        (e.g. SUSE:Maintenance:123:45678 has a request id of 45678) if
        needed.

        """
        reqid = cls.COMPLETE_REQUEST_ID_SRE.match(request_id)
        if reqid:
            return reqid.group('req')
        return request_id

    def _infer_assignment(self):
        def is_assignment(event):
            return "Review got assigned" in event.description

        def is_unassignment(event):
            return ("Review got reopened" in event.description and
                    "unassign" in event.comment)

        def is_accepted(event):
            return ("Review got accepted in event.description" and
                    (not event.comment or
                     "[qamosc]::accept" in event.comment))
        assignments = []
        unassignment_user_regex = re.compile(
            "\[oscqam\]::unassign::(?P<user>\w+)::.*"
        )
        unassignment_group_regex = re.compile(
            "\[oscqam\]::unassign::.+::(?P<group>.*)"
        )
        assignment_user_regex = re.compile(
            "review assigend to user (?P<user>\w+)"
        )
        assignment_group_regex = re.compile("review for group (?P<group>.+)")
        prev_event = None
        was_unassignment = False
        for curr_event in self.statehistory:
            if is_assignment(curr_event):
                user_match = assignment_user_regex.match(prev_event.comment)
                group_match = assignment_group_regex.match(curr_event.comment)
                if not user_match or not group_match:
                    logger.debug("Assign incorrect format: %s. %s",
                                 prev_event.comment, curr_event.comment)
                    continue
                assignment = self.Assignment(
                    User.by_name(self.remote, user_match.group('user')),
                    Group.for_name(self.remote, group_match.group('group'))
                )
                assignments.append(assignment)
            elif is_unassignment(curr_event):
                # Kind of ugly and *should* use a state-machine here.
                was_unassignment = True
            elif was_unassignment:
                user_match = unassignment_user_regex.match(prev_event.comment)
                group_match = unassignment_group_regex.match(curr_event.comment)
                if not user_match or not group_match:
                    logger.debug("Unassign incorrect format: %s. %s",
                                 prev_event.comment, curr_event.comment)
                    was_unassignment = False
                    continue
                assignment = self.Assignment(
                    User.by_name(self.remote, user_match.group('user')),
                    Group.for_name(self.remote, group_match.group('group'))
                )
                if assignment in assignments:
                    assignments.remove(assignment)
            elif is_accepted(curr_event):
                user = User.by_name(self.remote, curr_event.who)
                possible = [a for a in assignments if a.user == user]
                if possible:
                    group = possible[0].group
                    assignment = self.Assignment(user, group)
                    if assignment in assignments:
                        assignments.remove(assignment)
            prev_event = curr_event
        return assignments

    def __eq__(self, other):
        project = self.actions[0].src_project
        other_project = other.actions[0].src_project
        return (self.reqid == other.reqid and
                project == other_project)

    def __hash__(self):
        hash_parts = [self.reqid]
        if self.src_project:
            hash_parts.append(self.src_project)
        hashes = [hash(part) for part in hash_parts]
        return sum(hashes)

    def __str__(self):
        return self.reqid

    def unicode(self):
        return str(self)


class Template(object):
    """Facade to web-based templates.
    The templates can be found in:

    ``http://qam.suse.de/testreports/``
    """
    STATUS_SUCCESS = 0
    STATUS_FAILURE = 1
    STATUS_UNKNOWN = 2
    base_url = "http://qam.suse.de/testreports/"

    @total_ordering
    class Rating(object):
        """Store the template's rating.
        """
        def __init__(self, rating):
            self.rating = rating
            self.mapping = {
                'critical': 0,
                'important': 1,
                'moderate': 2,
                'low': 3,
                '': 4
            }

        def __lt__(self, other):
            return (self.mapping.get(self.rating, 10) <
                    self.mapping.get(other.rating, 10))

        def __eq__(self, other):
            return self.rating == other.rating

        def __str__(self):
            return self.rating

    def get_testreport_web(log_path):
        """Load the template belonging to the request from
        http://qam.suse.de/testreports/.

        :param request: The request this template is associated with.
        :type request: L{oscqam.models.Request}

        :return: Content of the log-file as string.

        """
        try:
            with contextlib.closing(urllib2.urlopen(log_path)) as log_file:
                return log_file.read()
        except urllib2.URLError:
            raise TemplateNotFoundError(log_path)

    def __init__(self, request, tr_getter = get_testreport_web):
        """Create a template from the given request.

        :param request: The request the template is associated with.
        :type request: L{oscqam.models.Request}.

        :param tr_getter: Function that can load the template's log file based
                          on the request. Will default to loading testreports
                          from http://qam.suse.de.

        :type tr_getter: Function: L{oscqam.models.Request} -> L{str}

        """
        self.log_entries = {}
        self.log_path = tr_getter(
            "{base}{prj}:{reqid}/log".format(base = self.base_url,
                                             prj = request.src_project,
                                             reqid = request.reqid)
        )
        self.parse_log(self.log_path)

    @property
    def status(self):
        summary = self.log_entries['SUMMARY']
        if summary.upper() == "PASSED":
            return Template.STATUS_SUCCESS
        elif summary.upper() == "FAILED":
            return Template.STATUS_FAILURE
        return Template.STATUS_UNKNOWN

    def parse_log(self, log):
        """Parses the header of the log into the log_entries dictionary.

        :type log: str
        """
        def split_packages(package_line):
            """Parse a 'Packages' line from a template-log into a list of individual
            packages.

            :type package_line: str

            :returns: [str]

            """
            return [v.strip() for v in package_line.split(",")]

        def split_products(product_line):
            """Split products into a list and strip SLE-prefix from each product.

            :type product_line: str

            :returns: [str]
            """
            products = map(str.strip, product_line.split("),"))
            products = [p if p.endswith(")") else p + ")" for p in products]
            return [re.sub("^SLE-", "", product, 1) for product in products]

        def split_srcrpms(srcrpm_line):
            """Parse 'SRCRPMs' from a template-log into a list.

            :type srcrpm_line: str

            :returns: [str]
            """
            return map(str.strip, srcrpm_line.split(","))

        for line in log.splitlines():
            # We end parsing at the results block.
            # We only need the header information.
            if "Test results by" in line:
                break
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, value = map(str.strip, line.split(":", 1))
            if key == 'Packages':
                value = split_packages(value)
            elif key == 'Products':
                value = split_products(value)
            elif key == "SRCRPMs":
                value = split_srcrpms(value)
            elif key == "Rating":
                value = self.Rating(value)
            else:
                value = value.strip()
            self.log_entries[key] = value


def monkeypatch():
    """Monkey patch retaining of history into the review class.
    """
    def monkey_patched_init(obj, review_node):
        # logger.debug("Monkeypatched init")
        original_init(obj, review_node)
        obj.statehistory = []
        for hist_state in review_node.findall('history'):
            obj.statehistory.append(osc.core.RequestHistory(hist_state))
    # logger.warn("Careful - your osc-version requires monkey patching.")
    original_init = osc.core.ReviewState.__init__
    osc.core.ReviewState.__init__ = monkey_patched_init

monkeypatch()
