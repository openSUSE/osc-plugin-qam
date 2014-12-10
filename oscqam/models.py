"""This module contains all models that are required by the QAM plugin to keep
everything in a consistent state.

"""
import contextlib
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
logger.setLevel(logging.DEBUG)


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

    def get(self, endpoint, params=None):
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

    def post(self, endpoint, data=None):
        url = '/'.join([self.remote, endpoint])
        remote = osc.core.http_POST(url, data=data)
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
    def parse_et(cls, remote, et, tag, wrapper_cls=None):
        """Recursively parses an element-tree instance.

        Will iterate over the tag as root-level.
        """
        if not wrapper_cls:
            wrapper_cls = cls
        objects = []
        for request in et.iter(tag):
            attribs = {}
            for attribute in request.attrib:
                attribs[attribute] = request.attrib[attribute]
            kwargs = {}
            for child in request:
                key = child.tag
                subchildren = list(child)
                if subchildren or child.attrib:
                    # Prevent that all children have the same class as the parent.
                    # This might lead to providing methods that make no sense.
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
        return self.name

    def __unicode__(self):
        return str(self).encode('utf-8')


class User(XmlFactoryMixin):
    """Wraps a user of the obs in an object.

    """
    endpoint = 'person'
    qam_regex = re.compile(".*qam.*")

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
                if User.qam_regex.match(group.name)]

    def __str__(self):
        return unicode(self)

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
    endpoint = 'request'

    OPEN_STATES = ['new', 'review']
    REVIEW_USER = 'BY_USER'
    REVIEW_GROUP = 'BY_GROUP'
    REVIEW_OTHER = 'BY_OTHER'

    def __init__(self, remote):
        self.remote = remote
        super(Request, self).__init__()
        self._groups = None
        self._packages = None

    def review_action(self, params, user=None, group=None, comment=None):
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

    def review_assign(self, group, reviewer, comment=None):
        params = {'cmd': 'assignreview',
                  'reviewer': reviewer.login}
        self.review_action(params, group=group, comment=comment)

    def review_accept(self, user=None, group=None, comment=None):
        params = {'cmd': 'changereviewstate',
                  'newstate': 'accepted'}
        self.review_action(params, user, group, comment)

    def review_add(self, user=None, group=None, comment=None):
        """Will add a new reviewrequest for the given user or group.

        """
        params = {'cmd': 'addreview'}
        self.review_action(params, user, group, comment)

    def review_decline(self, user=None, group=None, comment=None):
        """Will decline the reviewrequest for the given user or group.

        """
        params = {'cmd': 'changereviewstate',
                  'newstate': 'declined'}
        self.review_action(params, user, group, comment)

    def review_reopen(self, user=None, group=None, comment=None):
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
        for action in self.actions:
            if hasattr(action, 'src_project'):
                return action.src_project
        logger.info("This project has no source project: %s", self.reqid)

    @classmethod
    def for_user(cls, remote, user):
        params = {'user': user.login,
                  'view': 'collection',
                  'states': 'new,review'}
        return cls.parse(remote, remote.get(cls.endpoint, params))

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
        xpaths = ["(state/@name='{0}')".format('review')]
        for group in groups:
            name = get_group_name(group)
            xpaths.append(
                "(review[@by_group='{0}' and @state='new'])".format(name)
            )
        xpath = " and ".join(xpaths)
        params = {'match': xpath}
        params.update(kwargs)
        search = "/".join(["search", cls.endpoint])
        return cls.parse(remote, remote.get(search, params))

    @classmethod
    def by_id(cls, remote, req_id):
        endpoint = "/".join([cls.endpoint, req_id])
        # withfullhistory=1 breaks osc.core RequestState (history-elements
        # have not name)
        return cls.parse(remote, remote.get(endpoint, {'withfullhistory': 1}))[0]

    @classmethod
    def parse(cls, remote, xml):
        et = ET.fromstring(xml)
        requests = []
        for request in et.iter(cls.endpoint):
            try:
                req = Request(remote)
                req.read(request)
                requests.append(req)
            except osc.oscerr.APIError, e:
                logger.error(e.msg)
                pass
        return requests

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

    def __init__(self, project_name, request):
        """Create a new template from the given directory.
        """
        self.project = project_name
        self.request = request
        self.web_path = (Template.base_url + self.project + ":" +
                         self.request.reqid)
        self.log_entries = {}
        self.parse_log()

    @property
    def status(self):
        summary = self.log_entries['SUMMARY']
        if summary.upper() == "PASSED":
            return Template.STATUS_SUCCESS
        elif summary.upper() == "FAILED":
            return Template.STATUS_FAILURE
        return Template.STATUS_UNKNOWN

    def parse_log(self):
        """Parses the header of the log into the log_entries dictionary.
        """
        log_path = self.web_path + "/" + "log"
        try:
            with contextlib.closing(urllib2.urlopen(log_path)) as log_file:
                lines = log_file.read()
                for line in lines.splitlines():
                    # We end parsing at the results block.
                    # We only need the header information.
                    if "Test results by" in line:
                        break
                    try:
                        key, value = line.split(":", 1)
                        if key == 'Packages':
                            value = [v.strip() for v in value.split(",")]
                        elif key == 'Products':
                            value = value.replace("SLE-", "").strip()
                        else:
                            value = value.strip()
                        self.log_entries[key] = value
                    except ValueError:
                        pass
        except urllib2.URLError:
            logger.error("URL not found: %s", log_path)
            raise AttributeError("URL does not exist")

    @classmethod
    def for_request(cls, request):
        """Load the template for the given request.
        """
        request_project = request.src_project
        if not request_project:
            logger.info("No source project found.")
            return None
        try:
            return Template(request_project, request)
        except AttributeError:
            return None


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
